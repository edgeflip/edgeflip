from nose import tools

from core.utils import names


def test_parse_names():
    def try_parse_names(in_, out):
        tools.eq_(names.parse_names(in_), out)

    for (in_, out) in [
        ("John Smith", ("John", "Smith")),
        ("John D Smith", ("John D", "Smith")),
        ("John D. Smith", ("John D.", "Smith")),
        ("John Smith Jr", ("John", "Smith Jr")),
        ("John Smith, Jr.", ("John", "Smith, Jr.")),
        ("John D. Smith, Jr.", ("John D.", "Smith, Jr.")),
        ('Jimmy John Smith "II"', ('Jimmy John', 'Smith "II"')),
    ]:
        yield (try_parse_names, in_, out)
