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

from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx
from cloudify.exceptions import NonRecoverableError

import main.utils as utils
from main.saltapimgr.exceptions import LogicError


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.test_id = 'testId'
        self.ctx = None

    def _create_context(self, **kwargs):
        self.ctx = MockCloudifyContext(**kwargs)
        current_ctx.set(self.ctx)

    def tearDown(self):
        if self.ctx:
            current_ctx.clear()
            self.ctx = None

    def test_get_minion_id_runtime_properties(self):
        self._create_context(node_id='1',
                             node_name='node_name',
                             runtime_properties={'minion_id': self.test_id})
        minion_id = utils.get_minion_id()
        self.assertEqual(minion_id, self.test_id)

    def test_get_minion_id_node_properties(self):
        self._create_context(node_id='1',
                             node_name='node_name',
                             properties={'minion_id': self.test_id})
        minion_id = utils.get_minion_id()
        self.assertEqual(minion_id, self.test_id)

    def test_get_minion_id_no_properties(self):
        self.test_id = '1'
        self._create_context(node_id=self.test_id,
                             node_name='node_name',
                             properties={'minion_id': ''})
        minion_id = utils.get_minion_id()
        self.assertEqual(minion_id, self.test_id)

    def test_validate_properties_no_required(self):
        properties = {'salt_api_auth_data': '',
                      'logger_injection': ''}
        self.assertRaises(NonRecoverableError,
                          utils.validate_properties,
                          properties)

    def test_validate_properties_good_required(self):
        properties = {'salt_api_url': 'test_url',
                      'salt_api_auth_data': '',
                      'logger_injection': ''}
        utils.validate_properties(properties)

    def test_validate_properties_good_optional(self):
        properties = {'salt_api_url': 'test_url',
                      'minion_id': self.test_id,
                      'minion_config': '',
                      'salt_api_auth_data': {'eauth': 'qwerty'},
                      'logger_injection': {}}
        utils.validate_properties(properties)

    def test_validate_properties_wrong_optional(self):
        properties = {'salt_api_url': 'test_url',
                      'minion_id': self.test_id,
                      'minion_config': (),
                      'salt_api_auth_data': {'eauth': 'qwerty'},
                      'logger_injection': {}}
        self.assertRaises(NonRecoverableError,
                          utils.validate_properties,
                          properties)
        properties = {'salt_api_url': 'test_url',
                      'minion_id': self.test_id,
                      'minion_config': '',
                      'salt_api_auth_data': (),
                      'logger_injection': {}}
        self.assertRaises(NonRecoverableError,
                          utils.validate_properties,
                          properties)
        properties = {'salt_api_url': 'test_url',
                      'minion_id': self.test_id,
                      'minion_config': '',
                      'salt_api_auth_data': '',
                      'logger_injection': ()}
        self.assertRaises(NonRecoverableError,
                          utils.validate_properties,
                          properties)

    def test_instantiate_manager_no_token(self):
        self.test_id = '1'
        properties = {'salt_api_url': 'test_url',
                      'minion_id': '',
                      'minion_config': '',
                      'salt_api_auth_data': '',
                      'logger_injection': ''}
        self._create_context(node_id=self.test_id,
                             node_name='node_name',
                             properties=properties)
        self.assertRaises(LogicError, utils.instantiate_manager, False)
