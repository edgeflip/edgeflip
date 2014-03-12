import django.conf
from django.core.exceptions import ImproperlyConfigured
from django.utils import text


SEQUENCES = (tuple, list, set, frozenset)


class Settings(object):

    DEFAULTS = (
        ('DEBUG_URL', '/jsurls/'),
        ('INSTALL_PATH', None),
        ('JS_NAMESPACE', 'router'),
        ('URL_INCLUDES', ()),
        ('URL_EXCLUDES', ()),
        ('URL_NAMESPACES', ()),
    )

    @classmethod
    def read(cls, settings):
        new = cls()
        not_seq = []

        for (key, default) in cls.DEFAULTS:
            value = getattr(settings, 'JSURLS_' + key, default)
            setattr(new, key, value)
            if isinstance(default, tuple) and not isinstance(value, SEQUENCES):
                not_seq.append(key)

        if not_seq:
            seq_names = [type_.__name__ for type_ in SEQUENCES]
            raise ImproperlyConfigured(
                "the following settings must be but are not sequences ({}): {}"
                .format(
                    text.get_text_list(seq_names, 'or'),
                    text.get_text_list(not_seq, 'and'),
                )
            )

        return new

settings = Settings.read(django.conf.settings)
