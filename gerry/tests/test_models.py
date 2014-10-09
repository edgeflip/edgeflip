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
        ('Smith, PhD', 'SMITH', 'lname'),
        ('Smith, Jr.', 'SMITH', 'lname'),
        ('Smith I', 'SMITH', 'lname'),
        ('Smith II', 'SMITH', 'lname'),
        ('Smith IV', 'SMITH', 'lname'),
        ('Smith V', 'SMITH', 'lname'),
        ('Smith VII', 'SMITH', 'lname'),
        ('Smith IX', 'SMITH', 'lname'),
        ('Smith X', 'SMITH-X', 'lname'),
        ('Hsu Xi', 'HSU-XI', 'lname'),
    ]:
        yield (try_normalization, inp, out, feature)
