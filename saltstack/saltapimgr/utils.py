# coding=utf-8


import time

import requests

import yaml

import exceptions
import manager


_YAML_LOADER = yaml.SafeLoader
_YAML_DUMPER = yaml.SafeDumper


def token_valid(token):
    now = time.time()
    return now >= token['start'] and now < token['expire']


def send_login_request(session, base_url, auth_data):
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
    response = session.send(prepared_request)
    result = None
    if response.ok:
        result_raw = yaml.load(
                response.text,
                Loader = _YAML_LOADER
            )
        result = result_raw['return'][0]
    return response, result


def send_logout_request(session, base_url, token):
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
    response = session.send(prepared_request)
    result = None
    if response.ok:
        result_raw = yaml.load(
                response.text,
                Loader = _YAML_LOADER
            )
        result = result_raw['return']
    return response, result


def command_translation(command, use_yaml):
    if not command:
        raise exceptions.InvalidArgument(exceptions.NO_COMMAND_SPECIFIED)
    if not command.has_key('client'):
        command['client'] = manager._DEFAULT_CLIENT
    if use_yaml:
        command = yaml.dump(command, Dumper = _YAML_DUMPER)
    return command


def collection_translation(commands, use_yaml):
    if not commands:
        raise exceptions.InvalidArgument(
                exceptions.EMPTY_COMMAND_LIST_SPECIFIED)
    command_list = []
    for c in commands:
        if not c:
            raise exceptions.InvalidArgument(exceptions.NO_COMMAND_SPECIFIED)
        command_list.append(command_translation(c, False))
    if use_yaml:
        return yaml.dump(command_list, Dumper = _YAML_DUMPER)
    return command_list


def send_command_request(
        session,
        base_url,
        token,
        commands,
        single,
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
