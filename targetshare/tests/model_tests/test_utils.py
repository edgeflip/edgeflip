from nose import tools

from targetshare.models.relational.utils.enumstatus import OrderedStrEnum


try:
    unicode
except NameError:
    # In Python 3, unicode no longer exists; (it's just str)
    unicode = None


BlogPostStatus = None


def setup_module():
    global BlogPostStatus

    class BlogPostStatus(OrderedStrEnum):

        draft = 'draft'
        published = 'published'
        archived = 'archived'

        __order__ = 'draft, published, archived'


def test_get_ordinal():
    """get_ordinal(value) returns ordinal of value"""
    for (index, status) in enumerate(['draft', 'published', 'archived']):
        yield (tools.eq_, BlogPostStatus.get_ordinal(status), index)


def test_member_ordinals():
    """__member_ordinals__ reflects ordinal look-up"""
    yield (tools.eq_,
           BlogPostStatus.__member_ordinals__,
           {'draft': 0, 'published': 1, 'archived': 2})

    for element in BlogPostStatus.__member_ordinals__:
        yield (tools.assert_is_instance, element, BlogPostStatus)


def test_string_equal_comparisions():
    """enum members are equal to their string values"""
    for status in ('draft', 'published', 'archived'):
        member = BlogPostStatus(status)
        yield (tools.assert_equal, status, member)

        if unicode is not None:
            yield (tools.assert_equal, unicode(status), member)


def test_string_unequal_comparisons():
    """Ordered enum members may be inequality-compared to their string values"""
    for (operands, operators) in (
        (['draft', u'draft'], [tools.assert_less]),
        (['published', u'published'], [tools.assert_less_equal, tools.assert_greater_equal]),
        (['archived', u'archived'], [tools.assert_greater]),
    ):
        for operand in operands:
            for operator in operators:
                yield (operator, operand, BlogPostStatus.published)


def test_enum_unequal_comparisons():
    """Ordered enum members may be inequality-compared to other enum members"""
    for (operand, operators) in (
        (BlogPostStatus.draft, [tools.assert_less]),
        (BlogPostStatus.published, [tools.assert_less_equal, tools.assert_greater_equal]),
        (BlogPostStatus.archived, [tools.assert_greater]),
    ):
        for operator in operators:
            yield (operator, operand, BlogPostStatus.published)


def test_bad_comparisons():
    """Comparison to non-strings and undefined statuses raises an exception"""
    def try_bad_comparison(bad_value, exc_class):
        with tools.assert_raises(exc_class):
            bad_value < BlogPostStatus.published

    for (bad_value, exc_class) in (
        (None, TypeError),
        (1, TypeError),
        ('deleted', ValueError),
    ):
        yield (try_bad_comparison, bad_value, exc_class)


def test_enum_aliases():
    """Enums are free to define look-up aliases without affecting ordinals"""
    class RedundantStatus(OrderedStrEnum):

        draft = 'draft'
        unpublished = 'draft'
        published = 'published'
        archived = 'archived'

        __order__ = 'draft, unpublished, published, archived'

    yield (tools.eq_, RedundantStatus.draft.ordinal, RedundantStatus.unpublished.ordinal)
    yield (tools.eq_, RedundantStatus.draft, RedundantStatus.unpublished)
    yield (tools.assert_less, RedundantStatus.unpublished, RedundantStatus.archived)
