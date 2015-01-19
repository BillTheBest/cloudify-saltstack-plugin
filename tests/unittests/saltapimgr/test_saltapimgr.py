import unittest
import time
import main.saltapimgr.manager as manager
from main.saltapimgr.exceptions import LogicError


class TestSaltapimgr(unittest.TestCase):

    def test_clear_token_no_token(self):
        mgr = manager.SaltRESTManager('mocked_url')
        self.assertRaises(LogicError, mgr.clear_token,
                          manager.SaltRESTManager.THROW)
        mgr.clear_token()
        self.assertIsNone(mgr._session)
        self.assertIsNone(mgr.token)

    def test_clear_token_invalid_token(self):
        now = time.time()
        token = {'start': now - 1000, 'expire': now + 1000}
        mgr = manager.SaltRESTManager('mocked_url', token=token)
        self.assertRaises(LogicError, mgr.clear_token,
                          manager.SaltRESTManager.THROW)
        mgr.clear_token()
        self.assertIsNone(mgr._session)
        self.assertIsNone(mgr.token)

if __name__ == '__main__':
    unittest.main()
