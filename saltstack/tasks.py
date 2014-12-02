# coding=utf-8


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


import os
import subprocess
import time

import yaml

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError
from cloudify.exceptions import RecoverableError

import saltapimgr


_DEFAULT_MINION_ID_PATH = '/etc/salt/minion_id'
_DEFAULT_MINION_CONFIG_PATH = '/etc/salt/minion'
_DEFAULT_INSTALLATION_SCRIPT_PATH = 'utility/default_minion_installation.sh'
_YAML_LOADER = yaml.SafeLoader
_YAML_DUMPER = yaml.SafeDumper

def validate_context(context):

    def check_dict(Dict, dictname, required={}, optional={}):
        def check_key(key, Type, required):
            if required and key not in Dict:
                raise NonRecoverableError(
                    'Invalid configuration: "{0}" should contain key "{1}"'
                    .format(dictname, key)
                )
            if key in Dict and not isinstance(Dict[key], Type):
                raise NonRecoverableError(
                    'Invalid configuration: Key "{0}" from "{1}" should be '
                    'of type {3}'.format(key, dictname, Type)
                )
        for key, Type in required.iteritems():
            check_key(key, Type, True)
        for key, Type in optional.iteritems():
            check_key(key, Type, False)

    check_dict(
        context, 'properties',
        required={'master_ssh_user': basestring,
                  'master_private_ssh_key': basestring,
                  'salt_api_url': basestring},
        optional={'minion_config': dict,
                  'salt_api_auth_data': dict,
                  'logger_injection': dict}
    )

    if 'salt_api_auth_data' in context:
        check_dict(
            context['salt_api_auth_data'], 'salt_api_auth_data',
            required={'eauth': basestring}
        )

    if 'logger_injection' in context:
        check_dict(
            context['logger_injection'], 'logger_injection',
            required={'level': basestring},
            optional={'show_auth': basestring}
        )


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


@operation
def install_minion(*args, **kwargs):
    validate_context(ctx.node.properties)

    def do_install_minion():
        command = get_installation_script()
        ctx.logger.info('Installing Salt minion using {0}'.format(command))
        try:
            output = subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                shell=True
            )
        except subprocess.CalledProcessError as e:
            ctx.logger.error(format_output(command, e.output))
            raise NonRecoverableError('Failed to install Salt minion.')
        else:
            ctx.logger.debug(format_output(command, output))
            verify_installation()

    def get_installation_script():
        command = ctx.node.properties.get('minion_installation_script', None)
        if not command:
            command = get_default_installation_script()
        elif not os.path.isfile(command):
            raise NonRecoverableError(
                'Installation script {0} does not exist'.format(command)
            )
        return command

    def get_default_installation_script():
        ctx.logger.debug('Installation script not provided, using default.')
        return os.path.join(
            os.path.dirname(__file__),
            *_DEFAULT_INSTALLATION_SCRIPT_PATH.split('/')
        )

    def format_output(command, output):
        msg_header = '{0} output:'.format(command)
        msg_footer = '---END OF OUTPUT FROM {0}---'.format(command)
        return '{0}\n{1}\n{2}'.format(msg_header, output, msg_footer)

    def verify_installation():
        try:
            subprocess.call(['salt-minion', '--version'])
        except OSError:
            raise NonRecoverableError(
                'Script ran successfully, but Salt minion was not installed.'
            )
        else:
            ctx.logger.info('Salt minion installed successfully.')

    try:
        subprocess.call(['salt-minion', '--version'])
    except OSError:
        do_install_minion()
    else:
        ctx.logger.info('Salt minion is already installed.')


@operation
def configure_minion(*args, **kwargs):
    validate_context(ctx.node.properties)

    def load_minion_config(path=_DEFAULT_MINION_CONFIG_PATH):
        ctx.logger.debug('Loading minion configuration from {0}'.format(path))
        try:
            with open(path, 'r') as f:
                config = yaml.load(f.read(), Loader=_YAML_LOADER)
                if config:
                    return config
                else:
                    return {}
        except OSError:
            ctx.logger.warn(
                'Minion configuration file {0} does not exist. '
                'Assuming empty configuration.'.format(path)
            )
            return {}

    def write_to_protected_file(data, path):
        p = subprocess.Popen(
            ['sudo', 'tee', path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        output = p.communicate(input=data)
        message = 'sudo tee {0} output:\n{1}'.format(path, output)

        p.wait()
        if p.returncode != 0:
            ctx.logger.error(message)
            raise RecoverableError(
                'Failed to write to file {0}.'.format(path)
            )
        else:
            ctx.logger.debug(message)

    def save_minion_config(config, path=_DEFAULT_MINION_CONFIG_PATH):
        ctx.logger.debug('Writing minion configuration to {0}'.format(path))
        data = yaml.dump(
            config,
            default_flow_style=False,
            Dumper=_YAML_DUMPER
        )
        write_to_protected_file(data, path)

    def save_minion_id(minion_id, path=_DEFAULT_MINION_ID_PATH):
        ctx.logger.debug('Writing minion id to {0}'.format(path))
        write_to_protected_file(minion_id, path)

    ctx.logger.info('Updating minion configuration with blueprint data...')

    subprocess.call(['sudo', 'service', 'salt-minion', 'stop'])
    config = load_minion_config()
    config.update(ctx.node.properties['minion_config'])
    save_minion_config(config)

    minion_id = ctx.node.properties['minion_id']
    if not minion_id:
        minion_id = ctx.instance.id
    save_minion_id(minion_id)
    ctx.instance.runtime_properties['minion_id'] = minion_id

    ctx.logger.info('Minion configuration updated successfully.')

# TODO: this operation does three different things, can we split it some way
# or give it a different name?
@operation
def start_minion(*args, **kwargs):
    validate_context(ctx.node.properties)

    def start_service():
        ctx.logger.info('Starting salt minion')
        subprocess.call(['sudo', 'service', 'salt-minion', 'start'])

    def authorize_minion(minion_id):
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

    def execute_initial_state(minion_id):
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

    def append_grains(minion_id):
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

    minion_id = ctx.instance.runtime_properties['minion_id']
    start_service()
    authorize_minion(minion_id)
    append_grains(minion_id)
    execute_initial_state(minion_id)


@operation
def stop_minion(*args, **kwargs):
    validate_context(ctx.node.properties)
    ctx.logger.info('Nothing to do.  We do not stop salt-minion service '
                    'because there may be multiple minions running on '
                    'the same machine.')
