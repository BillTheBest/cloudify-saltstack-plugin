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


NO_AUTH_DATA = 1
NO_TOKEN_TO_CLEAR = 2
TOKEN_HAS_EXPIRED = 3
TOKEN_IS_STILL_VALID = 4
NO_COMMAND_SPECIFIED = 5
EMPTY_COMMAND_LIST_SPECIFIED = 6


class LogicError(Exception):

    _NO_AUTH_DATA_MSG = '{0} {1}'.format(
            'No authentication data provided.',
            'Cannot open a session.')
    _NO_TOKEN_TO_CLEAR_MSG = '{0} {1}'.format(
            'There are no open sessions.',
            'No token to clear.')
    _TOKEN_HAS_EXPIRED_MSG = 'The token has expired.'
    _TOKEN_IS_STILL_VALID_MSG = '{0} {1}'.format(
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

    _NO_COMMAND_SPECIFIED_MSG = '{0} {1}'.format(
            'An empty command dictionary has been specified.',
            'Nothing to send.')
    _EMPTY_COMMAND_LIST_SPECIFIED_MSG = '{0} {1}'.format(
            'An empty command list has been specified.',
            'Nothing to send.')

    _REASON_TO_MESSAGE = {
            NO_COMMAND_SPECIFIED: _NO_COMMAND_SPECIFIED_MSG,
            EMPTY_COMMAND_LIST_SPECIFIED: _EMPTY_COMMAND_LIST_SPECIFIED_MSG
        }

    def __init__(self, reason):
        super(InvalidArgument, self).__init__(
                self._REASON_TO_MESSAGE[reason])
