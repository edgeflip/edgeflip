import unittest
from demo.datastructs import unidecodeSafe

class TestTimer(unittest.TestCase):
    def test___init__(self):
        # timer = Timer()
        assert False # TODO: implement your test here

    def test_elapsedPr(self):
        # timer = Timer()
        # self.assertEqual(expected, timer.elapsedPr(precision))
        assert False # TODO: implement your test here

    def test_elapsedSecs(self):
        # timer = Timer()
        # self.assertEqual(expected, timer.elapsedSecs())
        assert False # TODO: implement your test here

    def test_reset(self):
        # timer = Timer()
        # self.assertEqual(expected, timer.reset())
        assert False # TODO: implement your test here

    def test_stderr(self):
        # timer = Timer()
        # self.assertEqual(expected, timer.stderr(txt))
        assert False # TODO: implement your test here

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
        assert False # TODO: implement your test here

    def test___str__(self):
        # user_info = UserInfo(uid, first_name, last_name, sex, birthday, city, state)
        # self.assertEqual(expected, user_info.__str__())
        assert False # TODO: implement your test here

class TestFriendInfo(unittest.TestCase):
    def test___init__(self):
        # friend_info = FriendInfo(primId, friendId, first_name, last_name, sex, birthday, city, state, primPhotoTags, otherPhotoTags, mutual_friend_count)
        assert False # TODO: implement your test here

class TestEdge(unittest.TestCase):
    def test___init__(self):
        # edge = Edge(primInfo, secInfo)
        assert False # TODO: implement your test here

    def test___str__(self):
        # edge = Edge(primInfo, secInfo)
        # self.assertEqual(expected, edge.__str__())
        assert False # TODO: implement your test here

    def test_isBidir(self):
        # edge = Edge(primInfo, secInfo)
        # self.assertEqual(expected, edge.isBidir())
        assert False # TODO: implement your test here

    def test_toDict(self):
        # edge = Edge(primInfo, secInfo)
        # self.assertEqual(expected, edge.toDict())
        assert False # TODO: implement your test here

class TestEdgeFromCounts(unittest.TestCase):
    def test___init__(self):
        # edge_from_counts = EdgeFromCounts(primInfo, secInfo, inPostLikes, inPostComms, inStatLikes, inStatComms, inWallPosts, inWallComms, inTags, outPostLikes, outPostComms, outStatLikes, outStatComms, outWallPosts, outWallComms, outTags, primPhotoTags, otherPhotoTags, mutuals, score)
        assert False # TODO: implement your test here

class TestEdgeStreamless(unittest.TestCase):
    def test___init__(self):
        # edge_streamless = EdgeStreamless(userInfo, friendInfo)
        assert False # TODO: implement your test here

    def test_isBidir(self):
        # edge_streamless = EdgeStreamless(userInfo, friendInfo)
        # self.assertEqual(expected, edge_streamless.isBidir())
        assert False # TODO: implement your test here

class TestEdgeSC1(unittest.TestCase):
    def test___init__(self):
        # edge_s_c1 = EdgeSC1(userInfo, friendInfo, userStreamCount)
        assert False # TODO: implement your test here

class TestEdgeSC2(unittest.TestCase):
    def test___init__(self):
        # edge_s_c2 = EdgeSC2(userInfo, friendInfo, userStreamCount, friendStreamCount)
        assert False # TODO: implement your test here

    def test_isBidir(self):
        # edge_s_c2 = EdgeSC2(userInfo, friendInfo, userStreamCount, friendStreamCount)
        # self.assertEqual(expected, edge_s_c2.isBidir())
        assert False # TODO: implement your test here

class TestEdgeAggregator(unittest.TestCase):
    def test___init__(self):
        # edge_aggregator = EdgeAggregator(edgesSource, aggregFunc, requireIncoming, requireOutgoing)
        assert False # TODO: implement your test here

    def test_isBidir(self):
        # edge_aggregator = EdgeAggregator(edgesSource, aggregFunc, requireIncoming, requireOutgoing)
        # self.assertEqual(expected, edge_aggregator.isBidir())
        assert False # TODO: implement your test here

if __name__ == '__main__':
    unittest.main()
