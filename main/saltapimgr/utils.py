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


import time

import requests

import yaml

import exceptions
import log
import manager


_YAML_LOADER = yaml.SafeLoader
_YAML_DUMPER = yaml.SafeDumper


def _log_http_request(logger, level, prefix, request):
    log.log(
            logger,
            level,
            '{0}: sending {1}, headers = {2}, body = \'{3}\''.format(
                    prefix,
                    str(request).strip(),
                    str(request.headers).strip(),
                    str(request.body).strip()
                )
        )


def token_valid(token):
    now = time.time()
    return now >= token['start'] and now < token['expire']


def send_login_request(session, base_url, auth_data, logger):
    data_as_yaml = yaml.dump(
            auth_data,
            Dumper = _YAML_DUMPER
        )
    request = requests.Request(
            method = 'POST',
            url = base_url + '/login',
            data = data_as_yaml,
            headers = {
                    'Accept': 'application/x-yaml',
                    'Content-Type': 'application/x-yaml'
                }
        )
    prepared_request = request.prepare()
    _log_http_request(logger, 'debug', 'login', prepared_request)
    response = session.send(prepared_request)
    result = None
    if response.ok:
        result_raw = yaml.load(
                response.text,
                Loader = _YAML_LOADER
            )
        result = result_raw['return'][0]
    return response, result


def send_logout_request(session, base_url, token, logger):
    data_as_yaml = yaml.dump(
            token,
            Dumper = _YAML_DUMPER
        )
    request = requests.Request(
            method = 'POST',
            url = base_url + '/logout',
            data = data_as_yaml,
            headers = {
                    'Accept': 'application/x-yaml',
                    'Content-Type': 'application/x-yaml',
                    'X-Auth-Token': token['token']
                }
        )
    prepared_request = request.prepare()
    _log_http_request(logger, 'debug', 'logout', prepared_request)
    response = session.send(prepared_request)
    result = None
    if response.ok:
        result_raw = yaml.load(
                response.text,
                Loader = _YAML_LOADER
            )
        result = result_raw['return']
    return response, result


def command_translation(command):
    if not command:
        raise exceptions.InvalidArgument(exceptions.NO_COMMAND_SPECIFIED)
    if not command.has_key('client'):
        command['client'] = manager._DEFAULT_CLIENT
    return command


def collection_translation(commands, logger, use_yaml):
    if not commands:
        raise exceptions.InvalidArgument(
                exceptions.EMPTY_COMMAND_LIST_SPECIFIED)
    command_list = [command_translation(c) for c in commands]
    log.debug(
            logger,
            'translation: translated to \'{0}\''.format(
                    str(command_list).strip()
                )
        )
    if use_yaml:
        command_list = yaml.dump(command_list, Dumper = _YAML_DUMPER)
    return command_list


def send_command_request(
        session,
        base_url,
        token,
        commands,
        single,
        logger,
        yaml_format):
    headers = {
            'Accept': 'application/x-yaml',
        }
    if token:
        headers['X-Auth-Token'] = token['token']
    if yaml_format:
        headers['Content-Type'] = 'application/x-yaml'
    request = requests.Request(
            method = 'POST',
            url = base_url,
            headers = headers,
            data = commands
        )
    prepared_request = request.prepare()
    _log_http_request(logger, 'debug', 'send', prepared_request)
    response = session.send(prepared_request)
    result = None
    if response.ok:
        result_raw = yaml.load(
                response.text,
                Loader = _YAML_LOADER
            )
        result = result_raw['return']
        if single:
            result = result[0]
    return response, result
