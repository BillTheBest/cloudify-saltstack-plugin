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


@operation
def install_minion(*args, **kwargs):
    def do_install_minion():
        command = get_installation_script()
        try:
            logs = subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                shell=True
            )
        except subprocess.CalledProcessError as e:
            report_error(command, 'exited abnormally', e.output)
        else:
            verify_installation(logs)

    def get_installation_script():
        command = ctx.node.properties['minion_installation_script']
        if not command:
            command = get_default_installation_script()
        elif not os.path.isfile(command):
            raise NonRecoverableError(
                'Installation script {0} does not exist'.format(command)
            )
        ctx.logger.info('Installing salt minion using {0}'.format(command))
        return command

    def get_default_installation_script():
        ctx.logger.info('Installation script not provided, using default.')
        return os.path.join(
            os.path.dirname(__file__),
            *_DEFAULT_INSTALLATION_SCRIPT_PATH.split('/')
        )

    def report_error(command, descr, logs):
        msg_header = '{0} {1}. Command output:\n'.format(command, descr)
        msg_footer = '---END OF OUTPUT FROM {0}---\n'.format(command)
        ctx.logger.error('{0}{1}{2}'.format(msg_header, logs, msg_footer))
        raise NonRecoverableError("Failed to install salt minion.")

    def verify_installation(logs):
        try:
            subprocess.call(['salt-minion', '--version'])
        except OSError:
            report_error(
                command,
                'ran successfully, but salt minion was not installed',
                logs
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

    def load_minion_config(path=DEFAULT_CONFIG_PATH):
        ctx.logger.info('Loading minion config from {0}'.format(path))
        with open(path, 'r') as f:
            config = yaml.load(f.read(), Loader=yaml.SafeLoader)
            if config:
                return config
            else:
                return {}

    def save_and_replace_file(data, path=_DEFAULT_MINION_CONFIG_PATH):
        # TODO: find an elegant way to do this, without temp file juggling.
        temp_file = '/tmp/cfy-temp-file'
        with open(temp_file, 'w+') as f:
            f.write(data)
        subprocess.call(['sudo', 'cp', '--remove-destination', temp_file, path])
        subprocess.call(['rm', temp_file])

    def save_minion_config(config, path=_DEFAULT_MINION_CONFIG_PATH):
        data = yaml.dump(
            config,
            default_flow_style=False,
            Dumper=_YAML_DUMPER
        )
        save_and_replace_file(data, path)

    def save_minion_id(minion_id, path=_DEFAULT_MINION_ID_PATH):
        save_and_replace_file(minion_id, path)

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

    ctx.logger.info('Updated configuration config.')


# TODO: this operation does three different things, can we split it some way
# or give it a different name?
@operation
def start_minion(*args, **kwargs):
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
            if [ $? -eq 0 ]; then exit 0; else exit 1; fi
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
            subprocess.check_call(get_auth_command(minion_id))
        except subprocess.CalledProcessError as e:
            raise NonRecoverableError('{0} authorization failed.'.format(minion_id))
        else:
            ctx.logger.info('{0} authorization successful.'.format(minion_id))

    def execute_initial_state(minion_id):
        host = ctx.node.properties['minion_config']['master']
        port = ctx.node.properties['salt_api_port']
        user = ctx.node.properties['master_ssh_user']
        salt_api_url = 'http://{0}:{1}'.format(host, port)
        auth_data = {'eauth': 'pam', 'username': user, 'password': 'vagrant'}
        mgr = saltapimgr.SaltRESTManager(salt_api_url, auth_data)

        ctx.logger.info('Connecting with Salt API')
        resp, result = mgr.log_in()
        if not resp.ok:
            ctx.logger.error('Got response {0}'.format(resp))
            ctx.logger.error('Result: {0}'.format(result))
            raise NonRecoverableError('Unable to connect with Salt API.')

        ping_minion = {'client': 'local', 'tgt': minion_id, 'fun': 'test.ping'}
        for i in xrange(10):
            time.sleep(2)
            resp, result = mgr.call(ping_minion)
            if resp.ok and minion_id in result[0]:
                break
        else:
            raise RecoverableError('{0} does not respond.'.format(minion_id))

        ctx.logger.info('Executing highstate on {0}'.format(minion_id))
        resp, result = mgr.highstate(minion_id)
        if not resp.ok:
            ctx.logger.error('Got response {0}'.format(resp))
            ctx.logger.error('Result: {0}'.format(result))
            raise NonRecoverableError('Unable to execute highstate.')

        ctx.logger.info('Disconnecting from Salt API')
        resp, result = mgr.log_out()
        if not resp.ok:
            raise NonRecoverableError('Unable to disconnect from Salt API.')

    minion_id = ctx.instance.runtime_properties['minion_id']
    start_service()
    authorize_minion(minion_id)
    execute_initial_state(minion_id)


@operation
def stop_minion(*args, **kwargs):
    ctx.logger.info('Nothing to do.  We do not stop salt-minion service because')
    ctx.logger.info('there may be multiple minions running on the same machine.')
