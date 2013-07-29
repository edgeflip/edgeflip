import re
import unittest
from datetime import date

from targetshare.datastructs import (
    Edge,
    FriendInfo,
    Timer,
    UserInfo,
    unidecodeSafe
)


class TestTimer(unittest.TestCase):

    def test___init__(self):
        # timer = Timer()
        timer = Timer()
        assert timer.start

    def test_elapsedPr(self):
        timer = Timer()
        assert re.search('\d+:\d+.\d+', timer.elapsedPr())

    def test_elapsedSecs(self):
        timer = Timer()
        assert timer.elapsedSecs()

    def test_reset(self):
        timer = Timer()
        orig_start_time = timer.start
        timer.reset()
        assert timer.start > orig_start_time


class TestUnidecodeSafe(unittest.TestCase):

    def test_unidecode_safe_raises_type_error_for_42(self):
        self.assertRaises(TypeError, lambda: unidecodeSafe(42))

    def test_unidecode_safe_raises_type_error_for_bytestring(self):
        self.assertRaises(TypeError, lambda: unidecodeSafe('bytestring'))

    def test_unidecode_safe_returns_Axcellent_for_unicode_string(self):
        self.assertEqual('Axcellent', unidecodeSafe(u'\xc3\x89xcellent'))

    def test_unidecode_safe_returns__for_None(self):
        self.assertEqual('?', unidecodeSafe(None))

    def test_unidecode_safe_returns__for_unicode_string(self):
        self.assertEqual('', unidecodeSafe(u''))

    def test_unidecode_safe_returns_foo_for_unicode_string(self):
        self.assertEqual('foo', unidecodeSafe(u'foo'))


class TestUserInfo(unittest.TestCase):

    def test___init__(self):
        # user_info = UserInfo(uid, first_name, last_name, sex, birthday, city, state)
        user_info = UserInfo(
            1, u'Test', u'User', 'test@example.com', 'Male',
            date(1984, 1, 1), u'Chicago', u'Illinois'
        )
        assert user_info
        self.assertEqual(user_info.id, 1)
        self.assertEqual(user_info.fname, 'Test')
        self.assertEqual(user_info.lname, 'User')
        self.assertEqual(user_info.email, 'test@example.com')
        self.assertEqual(user_info.gender, 'Male')
        self.assertEqual(user_info.birthday, date(1984, 1, 1))
        assert user_info.age
        self.assertEqual(user_info.city, 'Chicago')
        self.assertEqual(user_info.state, 'Illinois')

    def test___str__(self):
        user_info = UserInfo(
            1, u'Test', u'User', 'test@example.com', 'Male',
            date(1984, 1, 1), u'Chicago', u'Illinois'
        )
        assert user_info
        self.assertEqual(
            user_info.__str__(),
            '1 Test User Male 29 Chicago Illinois'
        )


class TestFriendInfo(unittest.TestCase):

    def test___init__(self):
        friend_info = FriendInfo(
            1, 2, u'Test', u'User', 'test@example.com', 'Male',
            date(1984, 1, 1), u'Chicago', u'Illinois', 1, 2, 3
        )
        self.assertEqual(friend_info.primPhotoTags, 1)
        self.assertEqual(friend_info.otherPhotoTags, 2)
        self.assertEqual(friend_info.mutuals, 3)


class TestEdge(unittest.TestCase):

    def test___init__(self):
        # edge = Edge(primInfo, secInfo)
        prim_info = UserInfo(
            1, u'Test', u'User', 'test@example.com', 'Male',
            date(1984, 1, 1), u'Chicago', u'Illinois'
        )
        sec_info = UserInfo(
            1, u'Test', u'User', 'test@example.com', 'Male',
            date(1984, 1, 1), u'Chicago', u'Illinois'
        )
        edge = Edge(prim_info, sec_info, 1, 1)
        self.assertEqual(edge.primary, prim_info)
        self.assertEqual(edge.secondary, sec_info)

    def test_toDict(self):
        prim_info = UserInfo(
            1, u'Test', u'User', 'test@example.com', 'Male',
            date(1984, 1, 1), u'Chicago', u'Illinois'
        )
        sec_info = UserInfo(
            1, u'Test', u'User', 'test@example.com', 'Male',
            date(1984, 1, 1), u'Chicago', u'Illinois'
        )
        edge = Edge(prim_info, sec_info, 1, 1)
        self.assertEqual(
            edge.toDict(),
            {
                'lname': u'User', 'city': u'Chicago', 'state': u'Illinois',
                'score': None, 'name': u'Test User', 'fname': u'Test',
                'gender': 'Male', 'age': 29, 'id': 1, 'desc': ''
            }
        )

if __name__ == '__main__':
    unittest.main()
