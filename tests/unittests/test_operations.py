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

from cloudify.exceptions import NonRecoverableError
from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx

from main import configure_minion
from main import install_minion


class TestOperations(unittest.TestCase):
    """Test some of the functions used in node lifecycle operations
    (not all of them can be reasonably tested)"""

    def test_load_minion_config(self):
        res = configure_minion._load_minion_config('dummy_minion_config.yaml')
        self.assertDictEqual(res, {'a': 1, 'b': {'c': 3, 'd': 4}})

    def test_load_minion_config_from_non_existing_file(self):
        res = configure_minion._load_minion_config('NonExistingFile')
        self.assertDictEqual(res, {}, 'Should return an empty dictionary.')

    def test_load_minion_config_from_path_that_cannot_be_read(self):
        self.assertRaises(NonRecoverableError,
                          configure_minion._load_minion_config,
                          './')

    def test_get_installation_script(self):
        ctx = MockCloudifyContext(node_id='1',
                                  node_name='node_name',
                                  properties={'minion_installation_script': '/bin/true'})
        current_ctx.set(ctx)
        self.assertEqual(install_minion._get_installation_script(),
                         '/bin/true')

    def test_get_installation_script_default_script(self):
        ctx = MockCloudifyContext(node_id='1',
                                  node_name='node_name',
                                  properties={'minion_installation_script': ''})
        current_ctx.set(ctx)
        self.assertRegexpMatches(install_minion._get_installation_script(),
                                 '.*main/scripts/default_minion_installation.sh')

    def test_get_installation_script_non_existing_file(self):
        ctx = MockCloudifyContext(node_id='1',
                                  node_name='node_name',
                                  properties={'minion_installation_script': 'NonExistingFile.sh'})
        current_ctx.set(ctx)
        self.assertRaises(NonRecoverableError,
                          install_minion._get_installation_script)

    def test_install_minion_failing_script(self):
        ctx = MockCloudifyContext(node_id='1',
                                  node_name='node_name',
                                  properties={'minion_installation_script': '/bin/false'})
        current_ctx.set(ctx)
        self.assertRaises(NonRecoverableError,
                          install_minion._install_minion)
