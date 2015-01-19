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


import unittest
import time

import main.saltapimgr.utils as utils
import main.saltapimgr.manager as manager
from main.saltapimgr.exceptions import InvalidArgument


class TestSaltapimgrUtils(unittest.TestCase):

    def test_command_translation_no_args(self):
        self.assertRaises(InvalidArgument, utils.command_translation, None)

    def test_command_translation_no_client(self):
        command = {'test': 'command'}
        out = utils.command_translation(command)
        self.assertEqual(out['client'], manager._DEFAULT_CLIENT)

    def test_command_translation_custom_client(self):
        test_client = 'test'
        command = {'client': test_client}
        out = utils.command_translation(command)
        self.assertEqual(out['client'], test_client)

    def test_collection_translation_no_args(self):
        self.assertRaises(InvalidArgument, utils.collection_translation,
                          None, None, False)

    def test_collection_translation_normal_commands(self):
        command = {'client': 'test'}
        commands = [command, ]
        out = utils.collection_translation(commands, None, False)
        self.assertEqual(out, commands)

    def test_collection_translation_yaml_commands(self):
        command = {'client': 'test'}
        commands = [command, ]
        test_out = '- {client: test}\n'
        out = utils.collection_translation(commands, None, True)
        self.assertEqual(test_out, out)

    def test_token_valid_valid(self):
        now = time.time()
        test_token = {'start': now - 1000, 'expire': now + 1000}
        self.assertTrue(utils.token_valid(test_token))

    def test_token_valid_expired(self):
        now = time.time()
        test_token = {'start': now - 2000, 'expire': now - 1000}
        self.assertFalse(utils.token_valid(test_token))

    def test_token_valid_future(self):
        now = time.time()
        test_token = {'start': now + 2000, 'expire': now + 3000}
        self.assertFalse(utils.token_valid(test_token))

    def test_token_valid_broken(self):
        now = time.time()
        test_token = {'start': now + 2000, 'expire': now - 3000}
        self.assertFalse(utils.token_valid(test_token))
