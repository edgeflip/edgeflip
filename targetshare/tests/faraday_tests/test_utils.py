from nose import tools

from targetshare.models.dynamo.base import utils


class TestCachedProperty(object):

    @classmethod
    def setup_class(cls):
        class CachedPropertyObject(object):

            def __init__(self):
                self.call_count = 0

            @utils.cached_property
            def method(self):
                self.call_count += 1
                return 55

        setattr(cls, CachedPropertyObject.__name__, CachedPropertyObject)

    def test_caching(self):
        obj = self.CachedPropertyObject()
        tools.eq_(vars(obj), {'call_count': 0})
        tools.eq_(obj.method, 55)
        tools.eq_(obj.method, 55)
        tools.eq_(vars(obj), {'call_count': 1, 'method': 55})

    def test_class_access(self):
        tools.assert_is_instance(self.CachedPropertyObject.method,
                                 utils.cached_property)


class TestClassProperty(object):

    @classmethod
    def setup_class(cls):
        class ClassPropertyObject(object):

            _value = 55

            @utils.class_property
            def method(kls):
                return kls._value

        setattr(cls, ClassPropertyObject.__name__, ClassPropertyObject)

    def test_class(self):
        tools.eq_(self.ClassPropertyObject.method, 55)

    def test_object(self):
        tools.eq_(self.ClassPropertyObject().method, 55)


class TestLazySequence(object):

    get_sequence = utils.LazySequence

    def test_lazy_init(self):
        iterable = iter([1, 2])
        seq = self.get_sequence(iterable)
        tools.assert_true(seq.iterable)
        tools.assert_false(list(seq._results.__iter__()))
        tools.eq_(list(iterable), [1, 2])

    def test_init_len(self):
        seq = self.get_sequence([1, 2])
        tools.eq_(len(seq), 2)
        tools.assert_is_none(seq.iterable)
        tools.eq_(list(seq._results.__iter__()), [1, 2])
        tools.assert_items_equal(seq, [1, 2])

    def test_bool_false(self):
        seq = self.get_sequence()
        tools.assert_false(seq)

    def test_bool_true_lazy(self):
        seq = self.get_sequence([1, 2])
        tools.assert_true(seq)
        tools.assert_true(seq.iterable)
        tools.eq_(list(seq._results.__iter__()), [1])

    def test_lazy_len(self):
        seq = self.get_sequence([1, 2])
        tools.assert_true(seq)
        tools.eq_(len(seq), 2)
        tools.assert_is_none(seq.iterable)
        tools.assert_items_equal(seq, [1, 2])

    def test_getitem_lazy(self):
        seq = self.get_sequence([1, 2, 3])
        tools.eq_(seq[1], 2)
        tools.assert_true(seq.iterable)
        tools.eq_(list(seq._results.__iter__()), [1, 2])

    def test_getslice_lazy(self):
        seq = self.get_sequence([1, 2, 3])
        sliced = seq[:2]
        tools.assert_is_not(sliced, seq)
        tools.assert_items_equal(sliced, [1, 2])
        tools.assert_true(seq.iterable)
        tools.eq_(list(seq._results.__iter__()), [1, 2])

    def test_count(self):
        iterable = iter([1, 2, 2, 2])
        seq = self.get_sequence(iterable)
        tools.eq_(seq.count(2), 3)
        tools.assert_false(list(iterable))

    def test_index_preexisting(self):
        iterable = iter([1, 2, 2, 2])
        seq = self.get_sequence(iterable)
        tools.eq_(seq[1], 2)
        tools.eq_(seq.index(2), 1)

    def test_index_advance(self):
        iterable = iter([1, 2, 2, 2])
        seq = self.get_sequence(iterable)
        tools.eq_(seq.index(2), 1)

    def test_index_missing(self):
        seq = self.get_sequence([1, 2, 2, 2])
        tools.assert_raises(ValueError, seq.index, 5)

    def test_contains_preexisting(self):
        iterable = iter([1, 2, 2, 2])
        seq = self.get_sequence(iterable)
        tools.eq_(seq[2], 2)
        tools.assert_in(2, seq)
        tools.assert_true(seq.iterable)
        tools.eq_(list(iterable), [2])

    def test_contains_advance(self):
        iterable = iter([1, 2, 2, 2])
        seq = self.get_sequence(iterable)
        tools.assert_in(2, seq)
        tools.assert_true(seq.iterable)
        tools.eq_(list(iterable), [2, 2])

    def test_ladd(self):
        seq = self.get_sequence([1, 2])
        result = seq + [3, 4]
        tools.assert_true(seq.iterable)
        tools.assert_true(result.iterable)
        tools.eq_(list(result), [1, 2, 3, 4])

    def test_radd(self):
        seq = self.get_sequence([1, 2])
        result = [3, 4] + seq
        tools.assert_is_none(seq.iterable)
        tools.eq_(result, [3, 4, 1, 2])
        tools.assert_items_equal(seq, [1, 2])

    def test_mul(self):
        seq = self.get_sequence([1, 2])
        result = seq * 2
        tools.assert_true(result.iterable)
        tools.assert_true(seq.iterable)
        tools.assert_items_equal(result, [1, 2, 1, 2])
        tools.assert_items_equal(seq, [1, 2])


class TestLazyList(TestLazySequence):

    # Inherits tests from parent!
    get_sequence = utils.LazyList

    def test_setslice_lazy(self):
        iterable = iter([1, 2, 3, 4])
        seq = self.get_sequence(iterable)
        seq[1:3] = (8, 9)
        tools.assert_true(seq.iterable)
        tools.eq_(list(iterable), [4])
        tools.assert_items_equal(seq, [1, 8, 9])

    def test_delslice_lazy(self):
        iterable = iter([1, 2, 3, 4])
        seq = self.get_sequence(iterable)
        del seq[0:2]
        tools.assert_true(seq.iterable)
        tools.eq_(list(iterable), [3, 4])
        tools.assert_false(seq)

    def test_extend_lazy(self):
        seq = self.get_sequence([1, 2])
        seq.extend([3, 4])
        tools.eq_(seq._results.__len__(), 0)
        tools.assert_items_equal(seq, [1, 2, 3, 4])

    def test_extend_eager(self):
        seq = self.get_sequence([1, 2])
        tools.assert_items_equal(seq, [1, 2])
        seq.extend([3, 4])
        tools.eq_(seq._results.__len__(), 4)
        tools.assert_items_equal(seq, [1, 2, 3, 4])

    def test_insert_lazy(self):
        seq = self.get_sequence(['a', 'c'])
        seq.insert(1, 'b')
        tools.assert_items_equal(seq._results.__iter__(), ['a', 'b'])
        tools.assert_items_equal(seq, ['a', 'b', 'c'])

    def test_pop_lazy(self):
        seq = self.get_sequence(['a', 'b', 'c'])
        tools.eq_(seq.pop(1), 'b')
        tools.assert_items_equal(seq._results.__iter__(), ['a'])
        tools.assert_items_equal(seq, ['a', 'c'])

    def test_remove_lazy(self):
        seq = self.get_sequence(['a', 'b', 'c'])
        seq.remove('b')
        tools.assert_items_equal(seq._results.__iter__(), ['a'])
        tools.assert_items_equal(seq, ['a', 'c'])

    def test_reverse(self):
        seq = self.get_sequence(['a', 'b', 'c'])
        seq.reverse()
        tools.assert_is_none(seq.iterable)
        tools.assert_items_equal(seq, ['c', 'b', 'a'])

    def test_sort(self):
        seq = self.get_sequence([10, 0, 'a'])
        seq.sort(key=lambda item: str(item))
        tools.assert_is_none(seq.iterable)
        tools.assert_items_equal(seq, [0, 10, 'a'])
