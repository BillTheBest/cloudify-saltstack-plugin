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
import errno

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError
from cloudify.exceptions import RecoverableError

import utils


_DEFAULT_MINION_CONFIG_PATH = '/etc/salt/minion'
_DEFAULT_MINION_KEYS_DIR = '/etc/salt/pki/minion/'
_DEFAULT_MINION_ID_PATH = '/etc/salt/minion_id'
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
    except EnvironmentError as e:
        if e.errno == errno.ENOENT:
            ctx.logger.warn(
                'Minion configuration file {0} does not exist. '
                'Assuming empty configuration.'.format(path)
            )
            return {}
        else:
            raise NonRecoverableError(
                'Error {0}: {1}'.format(e.errno, e.strerror)
            )


def _save_minion_config(config, path=_DEFAULT_MINION_CONFIG_PATH):
    ctx.logger.info('Writing minion configuration to {0}'.format(path))
    data = yaml.dump(
        config,
        default_flow_style=False,
        Dumper=_YAML_DUMPER
    )
    utils.write_protected_file(data, path)


def _save_minion_id(minion_id, path=_DEFAULT_MINION_ID_PATH):
    ctx.logger.info('Writing minion id to {0}'.format(path))
    utils.write_protected_file(minion_id, path)


def _authorize_minion(minion_id):
    if _is_authorized(minion_id):
        ctx.logger.info('Minion {0} is already authorized.'.format(minion_id))
    else:
        ctx.logger.info('Generating keys for minion {0}...'.format(minion_id))
        private, public = _generate_key(minion_id)
        try:
            path = _DEFAULT_MINION_KEYS_DIR
            subprocess.check_output(['sudo', 'mkdir', '-p', path])
        except subprocess.CalledProcessError as e:
            raise NonRecoverableError('Cannot create {0} directory: {1}\n'
                                      .format(path, e.output))
        utils.write_protected_file(private, path + 'minion.pem')
        utils.write_protected_file(public, path + 'minion.pub')
        ctx.logger.info('Minion {0} authorized.'.format(minion_id))


def _is_authorized(minion_id):
    mgr = utils.instantiate_manager()
    resp, result = mgr.accepted_minions()
    if resp.ok:
        accepted = result['data']['return']['minions']
        return minion_id in accepted
    else:
        ctx.logger.error('Got response {0}'.format(resp))
        raise NonRecoverableError(
            'Unable to get accepted minions from Salt API.'
        )


def _generate_key(minion_id):
    mgr = utils.instantiate_manager()
    resp, result = mgr.generate_accepted_key(minion_id)
    if resp.ok:
        ctx.logger.info('Generated key for minion {0}.'.format(minion_id))
        keys = result['data']['return']
        return keys['priv'], keys['pub']
    else:
        ctx.logger.error('Got response {0}'.format(resp))
        raise NonRecoverableError(
            'Unable to generate key for minion {0}.'.format(minion_id)
        )


@operation
def run(*args, **kwargs):
    utils.validate_context()
    minion_id = utils.get_minion_id()
    subprocess.call(['sudo', 'service', 'salt-minion', 'stop'])

    ctx.logger.info('Updating minion configuration with blueprint data...')
    config = _load_minion_config()
    config.update(ctx.node.properties['minion_config'])
    _save_minion_config(config)
    _save_minion_id(minion_id)
    ctx.logger.info('Minion configuration updated successfully.')

    _authorize_minion(minion_id)
