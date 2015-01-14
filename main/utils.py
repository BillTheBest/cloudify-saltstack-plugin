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

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

import saltapimgr


def get_minion_id():
    minion_id = ctx.instance.runtime_properties.get('minion_id', None)
    if not minion_id:
        minion_id = ctx.node.properties['minion_id']
        if not minion_id:
            minion_id = ctx.instance.id
        ctx.instance.runtime_properties['minion_id'] = minion_id

    return minion_id


def write_protected_file(data, path):
    proc = subprocess.Popen(
        ['sudo', 'tee', path],
        stdin=subprocess.PIPE,
        stdout=None,
        stderr=subprocess.PIPE
    )
    output = proc.communicate(input=data)
    message = 'sudo tee {0} output:\n{1}'.format(path, output)

    proc.wait() # may hang if tee outputs more than 64KB to stderr
    if proc.returncode != 0:
        ctx.logger.error(message)
        raise RecoverableError(
            'Failed to write to file {0}.'.format(path)
        )
    else:
        ctx.logger.debug(message)


def validate_properties(props):

    def check_dict(Dict, dictname, required={}, optional={}):
        def check_key(key, types, required):
            if required and key not in Dict:
                raise NonRecoverableError(
                    'Invalid configuration: "{0}" should contain key "{1}"'
                    .format(dictname, key)
                )
            if key in Dict and not isinstance(Dict[key], types):
                if isinstance(types, type):
                    valid_types = types.__name__
                else:
                    valid_types = ', '.join(t.__name__ for t in types)
                raise NonRecoverableError(
                    'Invalid configuration: wrong type of key "{0}" in "{1}".'
                    ' Valid type(s): {2}'.format(key, dictname, valid_types)
                )
        for key, types in required.iteritems():
            check_key(key, types, True)
        for key, types in optional.iteritems():
            check_key(key, types, False)

    check_dict(
        props, 'properties',
        required={'salt_api_url': basestring},
        optional={'minion_config': dict,
                  'salt_api_auth_data': dict,
                  'logger_injection': (basestring, dict)}
    )

    # We use empty string as a substitute for None, i.e. unset property
    # (Cloudify doesn't support None values in YAML files yet).
    if props['salt_api_auth_data'] != '':
        check_dict(
            props['salt_api_auth_data'], 'salt_api_auth_data',
            required={'eauth': basestring}
        )

    if props['logger_injection'] != '':
        check_dict(
            props['logger_injection'], 'logger_injection',
            optional={'level': basestring,
                      'show_auth': bool}
        )


def instantiate_manager(reuse_token=True):
    if reuse_token:
        token = ctx.instance.runtime_properties.get('token', None)
        if not token:
            token = ctx.node.properties.get('token', None)
    else:
        token = None

    api_url = ctx.node.properties['salt_api_url']
    auth_data = ctx.node.properties.get('salt_api_auth_data', None)
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

    mgr = saltapimgr.SaltRESTManager(
        api_url,
        auth_data=auth_data,
        token=token,
        session_options=session_options,
        root_logger=injected_logger,
        log_level=injected_logger_level,
        show_auth_data=injected_logger_show_auth
    )

    mgr.open_session()
    if not token:
        ctx.logger.info('Connecting to Salt API...')
        resp, result = mgr.log_in()
        if resp.ok:
            ctx.logger.info('Connected to Salt API.')
            ctx.instance.runtime_properties['token'] = mgr.token
        else:
            ctx.logger.error('Got response {0}'.format(resp))
            raise NonRecoverableError('Unable to connect with Salt API.')

    # Force the process to initiate TCP connection - first request
    # sent through a connection may take a long time and time out,
    # so we use a dummy request to "prepare" connection.
    mgr.ping('*')
    return mgr


def api_log_out(manager):
    resp, result = manager.log_out()
    if resp.ok:
        ctx.logger.debug('Token has been cleared')
    else:
        ctx.logger.warn('Unable to clear token.')
    del ctx.instance.runtime_properties['token']
    
