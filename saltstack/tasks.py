#!/usr/bin/python
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

import yaml

from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError


@operation
def install_minion(ctx, *args, **kwargs):
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
        command = ctx.properties['minion_installation_script']
        if not command:
            command = get_default_installation_script()
        elif not os.path.isfile(command):
            raise NonRecoverableError(
                'Installation script {} does not exist'.format(command)
            )
        ctx.logger.info('Installing salt minion using {}'.format(command))
        return command

    def get_default_installation_script():
        ctx.logger.info('Installation script not provided, using default.')
        return os.path.join(
            os.path.dirname(__file__),
            "default_minion_installation.sh"
        )

    def report_error(command, descr, logs):
        msg_header = '{} {}. Command output:\n'.format(command, descr)
        msg_footer = '---END OF OUTPUT FROM {}---\n'.format(command)
        ctx.logger.error('{}{}{}'.format(msg_header, logs, msg_footer))
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
def configure_minion(ctx, *args, **kwargs):
    DEFAULT_CONFIG_PATH = '/etc/salt/minion'

    def load_minion_config(path=DEFAULT_CONFIG_PATH):
        ctx.logger.info('Loading minion config from {}'.format(path))
        with open(path, 'r') as f:
            config = yaml.load(f.read(), Loader=yaml.SafeLoader)
            if config:
                return config
            else:
                return {}

    def save_minion_config(config, path=DEFAULT_CONFIG_PATH):
        # TODO: find an elegant way to do this, without temp file juggling.
        temp_file = '/tmp/cfy-salt-minion-config'
        with open(temp_file, 'w+') as f:
            f.write(yaml.dump(
                config,
                default_flow_style=False,
                Dumper=yaml.SafeDumper
            ))
        subprocess.call(['sudo', 'cp', '--remove-destination', temp_file, path])
        subprocess.call(['rm', temp_file])
        ctx.logger.info('Saved minion config to {}'.format(path))

    ctx.logger.info('Updating minion config with blueprint data')
    config = load_minion_config()
    config.update(ctx.properties['minion_config'])
    save_minion_config(config)


@operation
def start_minion(ctx, *args, **kwargs):
    ctx.logger.info('Starting salt minion')
    subprocess.call(['sudo', 'service', 'salt-minion', 'start'])

    minion_id = ctx.properties['minion_config']['id']

    def get_auth_command():
        key_file = ctx.properties['master_private_ssh_key']
        user = ctx.properties['master_ssh_user']
        host = ctx.properties['minion_config']['master']
        target = '{}@{}'.format(user, host)

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

    ctx.logger.info('Authorizing {}...'.format(minion_id))
    try:
        subprocess.check_call(get_auth_command())
    except subprocess.CalledProcessError as e:
        raise NonRecoverableError('{} authorization failed.'.format(minion_id))
    else:
        ctx.logger.info('{} authorization successful.'.format(minion_id))

@operation
def stop_minion(ctx, *args, **kwargs):
    ctx.logger.info('Nothing to do.  We do not stop salt-minion service because')
    ctx.logger.info('there may be multiple minions running on the same machine.')
