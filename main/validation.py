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


from cloudify.exceptions import NonRecoverableError


def validate_context(context):

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
        context, 'properties',
        required={'master_ssh_user': basestring,
                  'master_private_ssh_key': basestring,
                  'salt_api_url': basestring},
        optional={'minion_config': dict,
                  'salt_api_auth_data': dict,
                  'logger_injection': (basestring, dict)}
    )

    # We use empty string as a substitute for None, i.e. unset property
    # (Cloudify doesn't support None values in YAML files yet).
    if context['salt_api_auth_data'] != '':
        check_dict(
            context['salt_api_auth_data'], 'salt_api_auth_data',
            required={'eauth': basestring}
        )

    if context['logger_injection'] != '':
        check_dict(
            context['logger_injection'], 'logger_injection',
            optional={'level': basestring,
                      'show_auth': bool}
        )
