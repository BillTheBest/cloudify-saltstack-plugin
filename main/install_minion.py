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

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError
from cloudify.exceptions import RecoverableError

from validation import validate_context


_DEFAULT_INSTALLATION_SCRIPT_PATH = 'utility/default_minion_installation.sh'


def _install_minion():
    command = _get_installation_script()
    ctx.logger.info('Installing Salt minion using {0}'.format(command))
    try:
        output = subprocess.check_output(
            command,
            stderr=subprocess.STDOUT,
            shell=True
        )
    except subprocess.CalledProcessError as e:
        ctx.logger.error(_format_output(command, e.output))
        raise NonRecoverableError('Failed to install Salt minion.')
    else:
        ctx.logger.debug(_format_output(command, output))
        _verify_installation()


def _get_installation_script():
    command = ctx.node.properties.get('minion_installation_script', None)
    if not command:
        command = _get_default_installation_script()
    elif not os.path.isfile(command):
        raise NonRecoverableError(
            'Installation script {0} does not exist'.format(command)
        )
    return command


def _get_default_installation_script():
    ctx.logger.debug('Installation script not provided, using default.')
    return os.path.join(
        os.path.dirname(__file__),
        *_DEFAULT_INSTALLATION_SCRIPT_PATH.split('/')
    )


def _format_output(command, output):
    msg_header = '{0} output:'.format(command)
    msg_footer = '---END OF OUTPUT FROM {0}---'.format(command)
    return '{0}\n{1}\n{2}'.format(msg_header, output, msg_footer)


def _verify_installation():
    try:
        subprocess.call(['salt-minion', '--version'])
    except OSError:
        raise NonRecoverableError(
            'Script ran successfully, but Salt minion was not installed.'
        )
    else:
        ctx.logger.info('Salt minion installed successfully.')


@operation
def run(*args, **kwargs):
    validate_context(ctx.node.properties)
    try:
        subprocess.call(['salt-minion', '--version'])
    except OSError:
        _install_minion()
    else:
        ctx.logger.info('Salt minion is already installed.')
