from nose import tools

from gerry.models import normalize


def test_normalization():
    def try_normalization(inp, out, feature):
        result = normalize(feature, inp)
        tools.eq_(result, out)

    for (inp, out, feature) in [
        ('Jane', 'JANE', 'fname'),
        ('St Paul', 'ST-PAUL', 'city'),
        ('Illinois', 'IL', 'state'),
        ('Smith, Jr.', 'SMITH', 'lname'),
        ('Smith II', 'SMITH', 'lname'),
        ('Smith, PhD', 'SMITH', 'lname'),
    ]:
        yield (try_normalization, inp, out, feature)
