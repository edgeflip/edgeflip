from django.test.utils import override_settings
from django.utils.unittest import TestCase
from mock import Mock, patch

from core.db import locking


class Connections(dict):

    databases = {
        'default': {'NAME': 'FlippinDatabase'},
        'thisdb': {'NAME': 'AnotherDatabase'},
    }

    @classmethod
    def new(cls):
        return cls(default=Mock(), thisdb=Mock())

    def set_results(self, *results, **kws):
        cursor = Mock()
        cursor.fetchone.side_effect = results
        using = kws.get('using', 'default')
        self[using].cursor.return_value = cursor
        return cursor


patch_connections = patch.object(locking, 'connections', new_callable=Connections.new)


@patch_connections
class TestAdvisoryLockConfiguration(TestCase):

    def test_full_args(self, _connections_mock):
        lock = locking.AdvisoryLock(fullname='pudding', using='thisdb', timeout=0)
        self.assertEqual(lock.fullname, 'pudding')
        self.assertEqual(lock.using, 'thisdb')
        self.assertEqual(lock.timeout, 0)

    def test_defaults(self, _connections_mock):
        lock = locking.AdvisoryLock('pudding')
        self.assertEqual(lock.nickname, 'pudding')
        self.assertEqual(lock.fullname, 'FlippinDatabase:pudding')
        self.assertEqual(lock.using, 'default')
        self.assertEqual(lock.timeout, 3)

    @override_settings(ADVISORY_LOCK_DEFAULT_TIMEOUT=10)
    def test_global_default_timeout(self, _connections_mock):
        lock = locking.AdvisoryLock('pudding')
        self.assertEqual(lock.timeout, 10)

    @override_settings(ADVISORY_LOCK_PREFIX_DB_NAME=False)
    def test_nickname_no_db_prefix(self, _connections_mock):
        lock = locking.AdvisoryLock('pudding')
        self.assertEqual(lock.nickname, 'pudding')
        self.assertEqual(lock.fullname, 'pudding')

    @override_settings(ADVISORY_LOCK_NAME_PREFIX='flippin')
    def test_nickname_named_prefix(self, _connections_mock):
        lock = locking.AdvisoryLock('pudding')
        self.assertEqual(lock.nickname, 'pudding')
        self.assertEqual(lock.fullname, 'flippin:FlippinDatabase:pudding')

    @override_settings(ADVISORY_LOCK_NAME_PREFIX='flippin',
                       ADVISORY_LOCK_PREFIX_DB_NAME=False)
    def test_nickname_named_prefix_no_db(self, _connections_mock):
        lock = locking.AdvisoryLock('pudding')
        self.assertEqual(lock.nickname, 'pudding')
        self.assertEqual(lock.fullname, 'flippin:pudding')

    def test_set_full_name(self, _connections_mock):
        lock = locking.AdvisoryLock(fullname='pudding')
        lock.fullname = 'soup'
        self.assertEqual(lock.fullname, 'soup')

    def test_set_full_name_late(self, _connections_mock):
        lock = locking.AdvisoryLock('pudding')
        self.assertEqual(lock.nickname, 'pudding')

        lock.fullname = 'soup'
        self.assertEqual(lock.fullname, 'soup')
        self.assertIsNone(lock.nickname)


@patch_connections
class TestAdvisoryLockAcquisition(TestCase):

    def test_success(self, connections_mock):
        lock = locking.AdvisoryLock('pudding')
        cursor = connections_mock.set_results((1,))
        lock.acquire()
        cursor.execute.assert_called_once_with("SELECT GET_LOCK(%s, %s)", ("FlippinDatabase:pudding", 3))

    def test_error(self, connections_mock):
        lock = locking.AdvisoryLock('pudding')
        cursor = connections_mock.set_results((None,))
        with self.assertRaises(lock.AcquisitionFailure):
            lock.acquire()
        cursor.execute.assert_called_once_with("SELECT GET_LOCK(%s, %s)", ("FlippinDatabase:pudding", 3))

    def test_timeout(self, connections_mock):
        lock = locking.AdvisoryLock('pudding')
        cursor = connections_mock.set_results((0,))
        with self.assertRaises(lock.TimeoutError):
            lock.acquire()
        cursor.execute.assert_called_once_with("SELECT GET_LOCK(%s, %s)", ("FlippinDatabase:pudding", 3))


@patch_connections
class TestAdvisoryLockRelease(TestCase):

    def test_success(self, connections_mock):
        lock = locking.AdvisoryLock('pudding')
        cursor = connections_mock.set_results((1,))
        result = lock.release()
        self.assertTrue(result)
        cursor.execute.assert_called_once_with("SELECT RELEASE_LOCK(%s)", ("FlippinDatabase:pudding",))

    def test_noop(self, connections_mock):
        lock = locking.AdvisoryLock('pudding')
        cursor = connections_mock.set_results((None,))
        result = lock.release()
        self.assertFalse(result)
        cursor.execute.assert_called_once_with("SELECT RELEASE_LOCK(%s)", ("FlippinDatabase:pudding",))

    def test_error(self, connections_mock):
        lock = locking.AdvisoryLock('pudding')
        cursor = connections_mock.set_results((0,))
        with self.assertRaises(lock.ReleaseFailure):
            lock.release()
        cursor.execute.assert_called_once_with("SELECT RELEASE_LOCK(%s)", ("FlippinDatabase:pudding",))


@patch_connections
class TestAdvisoryLockIsFree(TestCase):

    def test_is_free(self, connections_mock):
        lock = locking.AdvisoryLock('pudding')
        cursor = connections_mock.set_results((1,))
        result = lock.is_free()
        self.assertTrue(result)
        cursor.execute.assert_called_once_with("SELECT IS_FREE_LOCK(%s)", ("FlippinDatabase:pudding",))

    def test_is_not_free(self, connections_mock):
        lock = locking.AdvisoryLock('pudding')
        cursor = connections_mock.set_results((0,))
        result = lock.is_free()
        self.assertFalse(result)
        cursor.execute.assert_called_once_with("SELECT IS_FREE_LOCK(%s)", ("FlippinDatabase:pudding",))

    def test_error(self, connections_mock):
        lock = locking.AdvisoryLock('pudding')
        cursor = connections_mock.set_results((None,))
        with self.assertRaises(lock.LockError):
            lock.is_free()
        cursor.execute.assert_called_once_with("SELECT IS_FREE_LOCK(%s)", ("FlippinDatabase:pudding",))


@patch_connections
class TestAdvisoryLockUser(TestCase):

    def test(self, connections_mock):
        lock = locking.AdvisoryLock('pudding')
        cursor = connections_mock.set_results((100,))
        result = lock.user()
        self.assertEqual(result, 100)
        cursor.execute.assert_called_once_with("SELECT IS_USED_LOCK(%s)", ("FlippinDatabase:pudding",))


@patch_connections
class TestAdvisoryLockContextManager(TestCase):

    def test(self, connections_mock):
        cursor = connections_mock.set_results((1,), (1,))
        with locking.AdvisoryLock('pudding') as lock:
            self.assertEqual(lock.fullname, "FlippinDatabase:pudding")
            cursor.execute.assert_any_call("SELECT GET_LOCK(%s, %s)", ("FlippinDatabase:pudding", 3))
        cursor.execute.assert_any_call("SELECT RELEASE_LOCK(%s)", ("FlippinDatabase:pudding",))
        self.assertEqual(cursor.execute.call_count, 2)


@patch_connections
class TestAdvisoryLockDecorator(TestCase):

    def test(self, connections_mock):
        cursor = connections_mock.set_results((1,), (1,))

        @locking.AdvisoryLock('pudding')
        def divider(a, b):
            return a / b

        with self.assertRaises(ZeroDivisionError):
            divider(1, 0)

        cursor.execute.assert_any_call("SELECT GET_LOCK(%s, %s)", ("FlippinDatabase:pudding", 3))
        cursor.execute.assert_any_call("SELECT RELEASE_LOCK(%s)", ("FlippinDatabase:pudding",))
        self.assertEqual(cursor.execute.call_count, 2)


class TestLockHelper(TestCase):

    def test_proxy(self):
        lock = locking.lock('pudding', using='thisdb', timeout=10)
        self.assertEqual(lock.nickname, 'pudding')
        self.assertEqual(lock.using, 'thisdb')
        self.assertEqual(lock.timeout, 10)

    @patch_connections
    def test_decorator(self, connections_mock):
        cursor = connections_mock.set_results((1,), (1,), using='thisdb')

        wrapped = locking.lock(lambda: 1 / 0, 'pudding', using='thisdb')
        with self.assertRaises(ZeroDivisionError):
            wrapped()

        cursor.execute.assert_any_call("SELECT GET_LOCK(%s, %s)", ("AnotherDatabase:pudding", 3))
        cursor.execute.assert_any_call("SELECT RELEASE_LOCK(%s)", ("AnotherDatabase:pudding",))
        self.assertEqual(cursor.execute.call_count, 2)

    @patch_connections
    def test_bare_decorator(self, connections_mock):
        cursor = connections_mock.set_results((1,), (1,))

        @locking.lock
        def divider(a, b):
            return a / b

        with self.assertRaises(ZeroDivisionError):
            divider(1, 0)

        name = "FlippinDatabase:core.tests.test_locking:divider"
        cursor.execute.assert_any_call("SELECT GET_LOCK(%s, %s)", (name, 3))
        cursor.execute.assert_any_call("SELECT RELEASE_LOCK(%s)", (name,))
        self.assertEqual(cursor.execute.call_count, 2)

    @patch_connections
    def test_named_method_decorator(self, connections_mock):
        cursor = connections_mock.set_results((1,), (1,))

        class Objectified(object):

            @classmethod
            @locking.lock('pudding')
            def races(cls, a, b):
                return a / b

        with self.assertRaises(ZeroDivisionError):
            Objectified.races(1, 0)

        cursor.execute.assert_any_call("SELECT GET_LOCK(%s, %s)", ("FlippinDatabase:pudding", 3))
        cursor.execute.assert_any_call("SELECT RELEASE_LOCK(%s)", ("FlippinDatabase:pudding",))
        self.assertEqual(cursor.execute.call_count, 2)


class TestLockMethodHelper(TestCase):

    @patch_connections
    def test_instance_decorator(self, connections_mock):
        cursor = connections_mock.set_results((1,), (1,), using='thisdb')

        class Objectified(object):

            @locking.lockingmethod(using='thisdb')
            def races(self, a, b):
                return a / b

        obj = Objectified()
        with self.assertRaises(ZeroDivisionError):
            obj.races(1, 0)

        name = "AnotherDatabase:core.tests.test_locking:Objectified.races"
        cursor.execute.assert_any_call("SELECT GET_LOCK(%s, %s)", (name, 3))
        cursor.execute.assert_any_call("SELECT RELEASE_LOCK(%s)", (name,))
        self.assertEqual(cursor.execute.call_count, 2)

    @patch_connections
    def test_class_decorator(self, connections_mock):
        cursor = connections_mock.set_results((1,), (1,), using='thisdb')

        class Objectified(object):

            @classmethod
            @locking.lockingmethod(using='thisdb')
            def races(cls, a, b):
                return a / b

        with self.assertRaises(ZeroDivisionError):
            Objectified.races(1, 0)

        name = "AnotherDatabase:core.tests.test_locking:Objectified.races"
        cursor.execute.assert_any_call("SELECT GET_LOCK(%s, %s)", (name, 3))
        cursor.execute.assert_any_call("SELECT RELEASE_LOCK(%s)", (name,))
        self.assertEqual(cursor.execute.call_count, 2)

    @patch_connections
    def test_bare_decorator(self, connections_mock):
        cursor = connections_mock.set_results((1,), (1,))

        class Objectified(object):

            @classmethod
            @locking.lockingmethod
            def races(cls, a, b):
                return a / b

        with self.assertRaises(ZeroDivisionError):
            Objectified.races(1, 0)

        name = "FlippinDatabase:core.tests.test_locking:Objectified.races"
        cursor.execute.assert_any_call("SELECT GET_LOCK(%s, %s)", (name, 3))
        cursor.execute.assert_any_call("SELECT RELEASE_LOCK(%s)", (name,))
        self.assertEqual(cursor.execute.call_count, 2)
