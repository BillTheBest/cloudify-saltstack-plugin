# coding=utf-8


import requests

import exceptions
import utils


_NON_DICT_OBJECTS_TREATED_AS_ITERABLE_BY_DEFAULT = (
        list,
        tuple,
        set,
        frozenset,
        xrange
    )
_DEFAULT_CLIENT = 'local'


class SaltRESTManager(object):
    '''Salt's REST API manager.

    Interesting methods:
        * __init__ - constructor,
        * call - raw function call,
        * log_in - opens a session,
        * clear_auth_data - clears authorisation data,
        * clear_token - clears a token, without closing an open session,
        * log_out - closes an open session,
        * logged_in - checks if a session is open.

    Interesting properties:
        * token - token structure, if one has been generated.
    '''

    def __init__(
            self,
            api_url,
            auth_data = None,
            token = None,
            session_options = None):
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
                    session options.
        '''
        self._session = None
        self._api_url = api_url
        self._auth_data = auth_data
        self._session_options = session_options
        self.token = token

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
            raise exceptions.LogicError(exceptions.NO_AUTH_DATA)
        if self._session is None:
            params = {}
            if self._session_options is not None:
                params = self._session_options
            self._session = requests.Session(**params)
        response, result = utils.send_login_request(
                self._session,
                self._api_url,
                self._auth_data)
        if result:
            self.token = result
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
        if self.auth_data is None and validation == SaltRESTManager.THROW:
            raise exceptions.LogicError(exception.NO_AUTH_DATA)
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
            if validation == SaltRESTManager.THROW:
                raise exceptions.LogicError(exceptions.NO_TOKEN_TO_CLEAR)
            else:
                return
        elif (utils.token_valid(self.token)
                and validation == SaltRESTManager.THROW):
            raise exception.LogicError(exception.TOKEN_IS_STILL_VALID)
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
                raise exceptions.LogicError(exceptions.NO_TOKEN_TO_CLEAR)
            elif not utils.token_valid(self.token):
                self.token = None
                raise exceptions.LogicError(exceptions.TOKEN_HAS_EXPIRED)
        except exceptions.LogicError:
            if validation == SaltRESTManager.THROW:
                raise
            else:
                return None
        response, result = utils.send_logout_request(
                self._session,
                self._api_url,
                self.token)
        self._session.close()
        self._session = None
        self.token = None
        return response, result

    DEFAULT_ACTION = 0
    INTERPRET_AS_COLLECTION = 1
    RAW_INTERPRETATION = 2

    def call(
            self,
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
            commands = utils.collection_translation(
                    func,
                    use_yaml
                )
        else:
            single = True
            commands = utils.command_translation(func, use_yaml)
        return utils.send_command_request(
                self._session,
                self._api_url,
                self.token,
                commands,
                single,
                use_yaml
            )
