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


import httpretty
import time
import unittest

from cloudify.exceptions import NonRecoverableError
from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx

from main.saltapimgr.manager import SaltRESTManager
from main.saltapimgr.exceptions import LogicError


class TestSaltapimgr(unittest.TestCase):

    def test_clear_token_no_token(self):
        mgr = SaltRESTManager('mocked_url')
        self.assertRaises(LogicError, mgr.clear_token,
                          SaltRESTManager.THROW)
        mgr.clear_token()
        self.assertIsNone(mgr._session)
        self.assertIsNone(mgr.token)

    def test_clear_token_invalid_token(self):
        now = time.time()
        token = {'start': now - 1000, 'expire': now + 1000}
        mgr = SaltRESTManager('mocked_url', token=token)
        self.assertRaises(LogicError, mgr.clear_token,
                          SaltRESTManager.THROW)
        mgr.clear_token()
        self.assertIsNone(mgr._session)
        self.assertIsNone(mgr.token)

    @httpretty.activate
    def test_log_in_successful(self):
        auth_data = {'eauth': 'pam',
                     'username': 'dummy_user',
                     'password': 'dummy password'}

        expected_request_headers = (
            "Host: localhost:8000\r\n"
            "Accept-Encoding: identity\r\n"
            "Content-Length: 61\r\n"
            "Content-Type: application/x-yaml\r\n"
            "Accept: application/x-yaml\r\n"
        )
        expected_request_body = ("{eauth: pam, password: dummy password, "
                                 "username: dummy_user}\n")

        mock_token = "22ed01b94ddc8671eadd58f2c099d7b31417873a"
        mocked_response_body = (
            "return:\n"
            "- eauth: pam\n"
            "  expire: 1421714252.331533\n"
            "  perms:\n"
            "  - .*\n"
            "  - '@wheel'\n"
            "  start: 1421671052.331532\n"
            "  token: {0}\n"
            "  user: vagrant\n".format(mock_token)
        )

        httpretty.register_uri(
            httpretty.POST,
            "http://localhost:8000/login",
            body=mocked_response_body,
            status=200
        )

        mgr = SaltRESTManager(api_url='http://localhost:8000')
        resp, result = mgr.log_in(auth_data=auth_data)

        self.assertEqual(str(httpretty.last_request().headers),
                         expected_request_headers)
        self.assertEqual(httpretty.last_request().body,
                         expected_request_body)
        self.assertEqual(result['token'], mock_token)

    @httpretty.activate
    def test_log_in_unauthorized(self):
        auth_data = {'eauth': 'pam',
                     'username': 'dummy_user',
                     'password': 'dummy password'}

        httpretty.register_uri(
            httpretty.POST,
            "http://localhost:8000/login",
            body="401 unauthorized\n",
            status=401
        )

        mgr = SaltRESTManager(api_url='http://localhost:8000')
        resp, result = mgr.log_in(auth_data=auth_data)
        self.assertIsNone(result)

    @httpretty.activate
    def test_log_out_expired_token(self):
        """An invalid token should not cause logout operation
        to abort. See also commit 7beeb84f07ac8.
        """
        httpretty.register_uri(
            httpretty.POST,
            "http://localhost:8000/logout",
            body="return: Welcome",
            status=200
        )
        mock_token = {'token': 'fa1afe1',
                      'start': '1421671052.331532',
                      'expire': '1421714252.331533'}
        mgr = SaltRESTManager(api_url='http://localhost:8000',
                              token=mock_token)

        mgr.open_session()
        mgr.log_out()

    def test_log_in_no_auth_data(self):
        mgr = SaltRESTManager(api_url='localhost:8000')
        self.assertRaises(LogicError, mgr.log_in)
