import json
import re
import sys
from optparse import make_option

from django.conf import settings
from django.core import urlresolvers
from django.core.management import BaseCommand, CommandError
from django.template.loader import render_to_string


GROUP_NAME_PATTERN = re.compile(r'\?P<[^>]+>')


def strip_names(pattern):
    """Strip group names from the given regular expression."""
    return GROUP_NAME_PATTERN.sub('', pattern)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--all', action='store_true', default=False, dest="compile_all",
                    help="Compile urls from all namespaces"),
        #make_options('--exclude', action='append',
        #             help="..."),
        #make_options('--include', action='append',
        #             help="..."),
        #make_option('--minify', action='store_true', default=False,
        #            help="..."), # TODO
    )

    def handle(self, *namespaces, **options):
        if namespaces and options['compile_all']:
            raise CommandError("option --all incompatible with namespace list")

        resolver = urlresolvers.get_resolver(None)
        namespace_dict = resolver.namespace_dict
        reverse_dict = resolver.reverse_dict

        if options['compile_all']:
            namspaces = namespace_dict.keys()

        if namespaces:
            raise NotImplementedError # TODO

        paths = {
            slug: bits[0] + (strip_names(pattern),)
            for (slug, (bits, pattern, _defaults)) in reverse_dict.iteritems()
            if isinstance(slug, basestring)
        }
        paths_encoded = json.dumps(paths, indent=4)

        javascript = render_to_string('jsurls/router.js', {
            'namespace': getattr(settings, 'JSURLS_NAMESPACE', None),
            # add 4-space indent for easy reading default block code:
            'paths': paths_encoded.replace('\n', '\n    '),
        })
        sys.stdout.write(javascript)
