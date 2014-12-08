###############################################################################
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
###############################################################################


import subprocess
import time
import yaml

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError
from cloudify.exceptions import RecoverableError

import saltapimgr
from validation import validate_context


def _start_service():
    ctx.logger.info('Starting salt minion')
    subprocess.call(['sudo', 'service', 'salt-minion', 'start'])


def _authorize_minion(minion_id):
    def get_auth_command(minion_id):
        key_file = ctx.node.properties['master_private_ssh_key']
        user = ctx.node.properties['master_ssh_user']
        host = ctx.node.properties['minion_config']['master']
        target = '{0}@{1}'.format(user, host)

        accept_minion_loop = """
        for i in `seq 1 10`; do
            sudo salt-key --yes --accept={0}
            sudo salt-key --list=accepted | tail -n +2 | grep {0}
            if [ $? -eq 0 ]; then exit 0; fi
            sleep 2
        done
        sudo salt-key --list=accepted | tail -n +2 | grep {0}
        if [ $? -eq 0 ]; then exit 0; else exit 254; fi
        """.format(minion_id)

        return [
            'ssh',
            '-i', key_file,
            '-oStrictHostKeyChecking=no',
            '-oUserKnownHostsFile=/dev/null',
            target,
            accept_minion_loop
        ]

    ctx.logger.info('Authorizing {0}...'.format(minion_id))
    try:
        output = subprocess.check_output(
            get_auth_command(minion_id),
            stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        ctx.logger.error('Minion authorization command output:\n'
                            '{0}'.format(e.output))
        if e.returncode == 255:
            raise NonRecoverableError('Unable to SSH into Salt master.')
        elif e.returncode == 254:
            raise NonRecoverableError(
                'Minion {0} did not report to Salt master '
                'and cannot be authorized.'.format(minion_id)
            )
        else:
            raise NonRecoverableError(
                'Minion {0} authorization exited with '
                'return code {1}.'.format(minion_id, e.returncode)
            )
    else:
        ctx.logger.debug('Minion authorization command output:\n'
                            '{0}'.format(output))
        ctx.logger.info('{0} authorization successful.'.format(minion_id))


def _instantiate_manager():
    api_url = ctx.node.properties['salt_api_url']
    auth_data = ctx.node.properties.get('salt_api_auth_data', None)
    token = ctx.node.properties.get('token', None)
    session_options = ctx.node.properties.get('session_options', None)
    logger_injection = ctx.node.properties.get('logger_injection', None)

    # UGH. we want to use 'None' default values inside yaml, but we cannot,
    # so we have to use empty strings there and convert them here.
    if not auth_data:
        auth_data = None
    if not token:
        token = None
    if not session_options:
        session_options = None
    if not logger_injection:
        logger_injection = None
    # END UGH.

    if logger_injection is not None:
        injected_logger = ctx.logger
        injected_logger_level = logger_injection.get('level', None)
        injected_logger_show_auth = logger_injection.get('show_auth', None)
    else:
        injected_logger = None
        injected_logger_level = None
        injected_logger_show_auth = None

    return saltapimgr.SaltRESTManager(
        api_url,
        auth_data=auth_data,
        token=token,
        session_options=session_options,
        root_logger=injected_logger,
        log_level=injected_logger_level,
        show_auth_data=injected_logger_show_auth
    )


# Conceptually this belongs to configuration, but since we are using
# Salt API to add grains to minions, we need to do start and authorize
# minion first.
def _append_grains(minion_id):
    # grains = a list of pairs
    grains = ctx.node.properties.get('grains', [])
    if grains:
        mgr = _instantiate_manager()
        mgr.log_in()
        mgr.ping(minion_id)
        added_grains = []
        for i in grains:
            grain = i.keys()[0]
            value = i.values()[0]
            response, result = mgr.append_grain(minion_id, grain, value)
            if response.ok:
                added_grains.append((grain, value))
        ctx.logger.info('Using additional grains: {0}.'.format(str(added_grains)))
        response, result = mgr.list_grains(minion_id)
        all_grains = []
        if response.ok:
            all_grains = result[minion_id]
        # TODO: Turn the following into some sort of debug.
        ctx.logger.info('A complete collection of currently used grains grains: {0}.'.format(str(all_grains)))
        resp, result = mgr.log_out()
        if resp.ok:
            ctx.logger.info('Token has been cleared')
        else:
            ctx.logger.error('Unable to clear token.')


def _execute_initial_state(minion_id):
    mgr = _instantiate_manager()

    ctx.logger.info('Connecting to Salt API...')
    resp, result = mgr.log_in()
    if not resp.ok:
        ctx.logger.error('Got response {0}'.format(resp))
        raise NonRecoverableError('Unable to connect with Salt API.')
    ctx.logger.info('Connected to Salt API.')

    ctx.logger.info('Pinging minion {0}...'.format(minion_id))
    for i in xrange(15):
        time.sleep(2)
        resp, result = mgr.ping(minion_id)
        if resp.ok and minion_id in result:
            break
    else:
        raise RecoverableError('{0} does not respond.'.format(minion_id))

    ctx.logger.info(
        'Executing highstate on minion {0}...'.format(minion_id)
    )
    resp, result = mgr.highstate(minion_id)
    if not resp.ok:
        ctx.logger.error('Got response {0}'.format(resp))
        raise NonRecoverableError(
            'Unable to execute highstate on minion {0}.'.format(minion_id)
        )
    ctx.logger.info('Executed highstate on minion {0}.'.format(minion_id))

    resp, result = mgr.log_out()
    if resp.ok:
        ctx.logger.debug('Token has been cleared')
    else:
        ctx.logger.warn('Unable to clear token.')


@operation
def run(*args, **kwargs):
    validate_context(ctx.node.properties)
    minion_id = ctx.instance.runtime_properties['minion_id']
    _start_service()
    _authorize_minion(minion_id)
    # note that highstate may depend on grains.
    _append_grains(minion_id)
    _execute_initial_state(minion_id)
