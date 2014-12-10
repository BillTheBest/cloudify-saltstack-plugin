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
import yaml

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError
from cloudify.exceptions import RecoverableError

from validation import validate_context


_DEFAULT_MINION_ID_PATH = '/etc/salt/minion_id'
_DEFAULT_MINION_CONFIG_PATH = '/etc/salt/minion'
_YAML_LOADER = yaml.SafeLoader
_YAML_DUMPER = yaml.SafeDumper


def _load_minion_config(path=_DEFAULT_MINION_CONFIG_PATH):
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

def _write_to_protected_file(data, path):
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

def _save_minion_config(config, path=_DEFAULT_MINION_CONFIG_PATH):
    ctx.logger.debug('Writing minion configuration to {0}'.format(path))
    data = yaml.dump(
        config,
        default_flow_style=False,
        Dumper=_YAML_DUMPER
    )
    _write_to_protected_file(data, path)

def _save_minion_id(minion_id, path=_DEFAULT_MINION_ID_PATH):
    ctx.logger.debug('Writing minion id to {0}'.format(path))
    _write_to_protected_file(minion_id, path)


@operation
def run(*args, **kwargs):
    validate_context(ctx.node.properties)

    ctx.logger.info('Updating minion configuration with blueprint data...')

    subprocess.call(['sudo', 'service', 'salt-minion', 'stop'])
    config = _load_minion_config()
    config.update(ctx.node.properties['minion_config'])
    _save_minion_config(config)

    minion_id = ctx.node.properties['minion_id']
    if not minion_id:
        minion_id = ctx.instance.id
    _save_minion_id(minion_id)
    ctx.instance.runtime_properties['minion_id'] = minion_id

    ctx.logger.info('Minion configuration updated successfully.')
