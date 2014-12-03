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


import requests

import exceptions
import log
import utils


_NON_DICT_OBJECTS_TREATED_AS_ITERABLE_BY_DEFAULT = (
        list,
        tuple,
        set,
        frozenset,
        xrange
    )
_DEFAULT_CLIENT = 'local'
_LOGGER_MODULE = 'salt'
_COVER_AUTH_DATA_WITH = '***'


class SaltRESTManager(object):
    '''Salt's REST API manager.

    Interesting methods:
        * __init__ - constructor,
        * call - raw function call,
        * log_in - opens a session,
        * clear_auth_data - clears authorisation data,
        * clear_token - clears a token, without closing an open session,
        * log_out - closes an open session,
        * logged_in - checks if a session is open,
        * ping - a `call' wrapper for the `test.ping' function,
        * highstate - a `call' wrapper for the `state.highstate'
                function,
        * append_grain - appends a given grain,
        * list_grains - lists all currently used grains.

    Interesting properties:
        * token - token structure, if one has been generated.
    '''

    def __init__(
            self,
            api_url,
            auth_data = None,
            token = None,
            session_options = None,
            root_logger = None,
            log_level = None,
            show_auth_data = False):
        '''Manager constructor. -> SaltRESTManager

        Check the Salt's API documentation for auth data and token
        dictionary structure reference.

        Check the Request's API documentation for possible session
        options (like disabling SSL certificate checking or supplying
        custom certificates).

        Arguments:
            * api_url = a mandatory URL to Salt REST API,
            * auth_data = an optional dictionary containing proper
                    authorisation data accepted by Salt `login'
                    API call,
            * token = an optional dictionary returned by Salt `login'
                    API call,
            * session_options = an optional dictionary containing
                    session options,
            * logger = if supplied, a child logger will be created
                    to dump debug information,
            * log_level = an optional log level to be set: can be
                    either a string or a predefined int from
                    the `logging' library,
            * show_auth_data = optionally the manager can be configured
                    not to cover auth data.
        '''
        self._session = None
        self._api_url = api_url
        self._auth_data = auth_data
        self._session_options = session_options
        self._show_auth_data = show_auth_data
        self.token = token
        self.logger = log.set_up_logger(root_logger, log_level)

    def logged_in(self):
        '''Check if a session is open. -> bool'''
        return self.token is not None and not utils.token_valid(self.token)

    def log_in(self, auth_data = None, session_options = None):
        '''Open a session. -> (requests.Response, result)

        `result' is a parsed output data structure.

        If auth data had not been supplied in the constructor,
        it can be here.

        Arguments:
            * auth_data = an optional dictionary containing
                    the authorisation data (explicit auth data has 
                    a higher priority).
        '''
        if auth_data is not None:
            self._auth_data = auth_data
        if session_options is not None:
            self._session_options = session_options
        if self._auth_data is None:
            log.error(
                    self.logger,
                    'log in: missing auth data'
                )
            raise exceptions.LogicError(exceptions.NO_AUTH_DATA)
        if self._session is None:
            params = {}
            if self._session_options is not None:
                params = self._session_options
            self._session = requests.Session(**params)
        log.debug(
                self.logger,
                'log in: logging in with auth data = {0}'
                ' and session options = {1}'.format(
                        log.cover_auth_data(
                                self._auth_data,
                                self._show_auth_data
                            ),
                        str(self._session_options).strip()
                    )
            )
        response, result = utils.send_login_request(
                self._session,
                self._api_url,
                self._auth_data,
                self.logger
            )
        if result:
            self.token = result
            log.info(
                    self.logger,
                    'log in: successfully logged in, token = {0}'.format(
                            str(self.token['token']).strip()
                        )
                )
            log.debug(
                    self.logger,
                    'log in: token = {0}'.format(
                            str(self.token).strip()
                        )
                )
        else:
            log.info(
                    self.logger,
                    'log in: failed to log in, HTTP return code = {0},'
                    ' reason = \'{1}\''. format(
                            str(response.status_code).strip(),
                            str(response.reason).strip()
                        )
                )
        return response, result

    THROW = 0
    SILENTLY_IGNORE = 1

    def clear_auth_data(self, validation = THROW):
        '''Clears authorisation data, if it has been specified.

        Arguments:
            * validation = if the function should raise an exception,
                    when there is no session to close, can be one of:
                ** THROW (default),
                ** SILENTLY_IGNORE.
        '''
        if self.auth_data is None:
            ERR_MSG = 'clear auth data: auth data not set'
            if validation == SaltRESTManager.THROW:
                log.error(self.logger, ERR_MSG)
                raise exceptions.LogicError(exception.NO_AUTH_DATA)
            else:
                log.warning(self.logger, ERR_MSG)
        self.auth_data = None

    def clear_token(self, validation = THROW):
        '''Clears the token without invalidating it.

        If `SILENTLY_IGNORE' has been specified, the token will be always
        cleared, even if it is still valid.

        Arguments:
            * validation = if the function should raise an exception,
                    when there is no session to close, can be one of:
                ** THROW (default),
                ** SILENTLY_IGNORE.
        '''
        if self.token is None:
            ERR_MSG = 'clear token: token not set'
            if validation == SaltRESTManager.THROW:
                log.error(self.logger, ERR_MSG)
                raise exceptions.LogicError(exceptions.NO_TOKEN_TO_CLEAR)
            else:
                log.warning(self.logger, ERR_MSG)
                return
        elif utils.token_valid(self.token):
            ERR_MSG = 'clear token: the token is still valid'
            if validation == SaltRESTManager.THROW:
                log.error(self.logger, ERR_MSG)
                raise exception.LogicError(exception.TOKEN_IS_STILL_VALID)
            else:
                log.warning(self.logger, ERR_MSG)
        self.token = None
        if self._session is not None:
            self._session.close()
            self._session = None

    def log_out(self, validation = THROW):
        '''Close the session, if it was open. -> (requests.Response, result)
        or None

        `result' is a parsed output data structure.

        Arguments:
            * validation = if the function should raise an exception,
                    when there is no session to close, can be one of:
                ** THROW (default),
                ** SILENTLY_IGNORE.
        '''
        try:
            if self.token is None:
                ERR_MSG = 'log out: no token to invalidate'
                raise exceptions.LogicError(exceptions.NO_TOKEN_TO_CLEAR)
            elif not utils.token_valid(self.token):
                ERR_MSG = 'log out: the token has already expired'
                self.token = None
                raise exceptions.LogicError(exceptions.TOKEN_HAS_EXPIRED)
        except exceptions.LogicError:
            if validation == SaltRESTManager.THROW:
                log.error(self.logger, ERR_MSG)
                raise
            else:
                log.warning(self.logger, ERR_MSG)
                return None, None
        log.debug(
                self.logger,
                'log out: invalidating token \'{0}\''.format(
                        str(self.token['token']).strip()
                    )
            )
        response, result = utils.send_logout_request(
                self._session,
                self._api_url,
                self.token,
                self.logger
            )
        if response.ok:
            log.info(
                    self.logger,
                    'log out: succesfully cleared token \'{0}\''.format(
                            str(self.token['token']).strip()
                        )
                )
        else:
            log.info(
                    self.logger,
                    'log out: failed to clear token \'{0}\','
                    ' HTTP return code = {1}, reason = \'{2}\''.format(
                            str(self.token['token']).strip(),
                            str(response.status_code).strip(),
                            str(response.reason).strip()
                        )
                )
        self._session.close()
        self._session = None
        self.token = None
        return response, result

    DEFAULT_ACTION = 0
    INTERPRET_AS_COLLECTION = 1
    RAW_INTERPRETATION = 2

    def call(self,
             func,
             action = DEFAULT_ACTION,
             use_yaml = True):
        '''Calls the requested function(s) using a raw call
        to the REST API. -> (requests.Response, results)

        `results' is a parsed output data structure in case of a single
        command or a list of such structures in case of multiple
        commands.

        The requested call may be a single function or a collection
        of functions. By default, iterable collections other than
        dictionaries and strings will be treated as multiple requests,
        unless explicitly specified otherwise.

        By default, the request will be in YAML, if possible,
        unless explicitly specified otherwise.

        If it is possible to inspect the parameters (if dictionary
        interface is available) and if `client' parameter has not been
        specified in the requested function(s) a `local' client will
        be added automatically.
        *TL;DR*: Automatic client injection will work only for a flat
        dict or an iterable collection of flat dicts.

        Check the Salt's API documentation for the function format
        reference.

        *TL;DR*: The preferred function format is a dict or a list
        of dicts.

        Arguments:
            * func = the requested function(s),
            * action = optional function interpretation style, one of:
                * DEFAULT_ACTION (default),
                * INTERPRET_AS_COLLECTION,
                * RAW_INTERPRETATION,
            * use_yaml = (yes by default) if the function call should be
                    in YAML.
        '''
        if (((action is None or action == SaltRESTManager.DEFAULT_ACTION)
                and isinstance(
                        func,
                        _NON_DICT_OBJECTS_TREATED_AS_ITERABLE_BY_DEFAULT))
                or action == SaltRESTManager.INTERPRET_AS_COLLECTION):
            single = False
            log.debug(self.logger, 'call: transforming collection into a list')
        else:
            single = True
            log.debug(self.logger, 'call: wrapping function in a list')
            func = [func]

        commands = utils.collection_translation(
            func,
            self.logger,
            use_yaml
        )
        response, result = utils.send_command_request(
                self._session,
                self._api_url,
                self.token,
                commands,
                single,
                self.logger,
                use_yaml
            )
        if response.ok:
            log.info(
                    self.logger,
                    'call: successfully called the given commands'
                )
            log.debug(
                    self.logger,
                    'call: results = \'{0}\''.format(
                            str(result).strip()
                        )
                )
        else:
            log.info(
                    self.logger,
                    'call: failed to call given commands,'
                    ' HTTP return code = {0}, reason = \'{1}\''.format(
                            str(response.status_code).strip(),
                            str(response.reason).strip()
                        )
                )
        return response, result

    def ping(self, target):
        '''Pings the given target(s). -> (requests.Response, result)'''
        return self.call(
                {'tgt': target, 'fun': 'test.ping'},
                use_yaml=True
            )

    def highstate(self, target):
        '''Executes `highstate' on given target.
        -> (requests.Response, result)
        '''
        return self.call(
                {'tgt': target, 'fun': 'state.highstate'},
                use_yaml=True
            )

    def append_grain(self, target, grain, value):
        '''Appends the given grain on all targets.
        -> (requests.Response, result)
        '''
        return self.call(
                {
                        'tgt': target,
                        'fun': 'grains.append',
                        'arg': [grain, value]
                    },
                use_yaml=True
            )

    def list_grains(self, target):
        '''Returns a list containg all grains.
        -> (requests.Response, result)
        '''
        return self.call(
                {'tgt': target, 'fun': 'grains.ls'},
                use_yaml=True
            )
