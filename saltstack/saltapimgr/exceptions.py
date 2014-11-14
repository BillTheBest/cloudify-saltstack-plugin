# coding=utf-8


NO_AUTH_DATA = 1
NO_TOKEN_TO_CLEAR = 2
TOKEN_HAS_EXPIRED = 3
TOKEN_IS_STILL_VALID = 4
NO_COMMAND_SPECIFIED = 5
EMPTY_COMMAND_LIST_SPECIFIED = 6


class LogicError(Exception):

    _NO_AUTH_DATA_MSG = '{} {}'.format(
            'No authentication data provided.',
            'Cannot open a session.')
    _NO_TOKEN_TO_CLEAR_MSG = '{} {}'.format(
            'There are no open sessions.',
            'No token to clear.')
    _TOKEN_HAS_EXPIRED_MSG = 'The token has expired.'
    _TOKEN_IS_STILL_VALID_MSG = '{} {}'.format(
            'The token is still valid.',
            'Force clearing of the token if You really want not to log out.'
        )

    _REASON_TO_MESSAGE = {
            NO_AUTH_DATA: _NO_AUTH_DATA_MSG,
            NO_TOKEN_TO_CLEAR: _NO_TOKEN_TO_CLEAR_MSG,
            TOKEN_HAS_EXPIRED: _TOKEN_HAS_EXPIRED_MSG,
            TOKEN_IS_STILL_VALID: _TOKEN_IS_STILL_VALID_MSG
        }

    def __init__(self, reason):
        super(LogicError, self).__init__(
                self._REASON_TO_MESSAGE[reason])


class InvalidArgument(Exception):

    _NO_COMMAND_SPECIFIED_MSG = '{} {}'.format(
            'An empty command dictionary has been specified.',
            'Nothing to send.')
    _EMPTY_COMMAND_LIST_SPECIFIED_MSG = '{} {}'.format(
            'An empty command list has been specified.',
            'Nothing to send.')

    _REASON_TO_MESSAGE = {
            NO_COMMAND_SPECIFIED: _NO_COMMAND_SPECIFIED_MSG,
            EMPTY_COMMAND_LIST_SPECIFIED: _EMPTY_COMMAND_LIST_SPECIFIED_MSG
        }

    def __init__(self, reason):
        super(InvalidArgument, self).__init__(
                self._REASON_TO_MESSAGE[reason])
