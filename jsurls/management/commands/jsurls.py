import json
import re
import sys
from itertools import chain
from optparse import make_option

from django.conf import settings
from django.core import urlresolvers
from django.core.management import BaseCommand, CommandError
from django.template.loader import render_to_string


GROUP_NAME_PATTERN = re.compile(r'\?P<[^>]+>')


def strip_names(pattern):
    """Strip group names from the given regular expression."""
    return GROUP_NAME_PATTERN.sub('', pattern)


def generate_reversals(resolver, namespace=None, prefix=''):
    """Generate flat tuples of URL reversal data from the given URL resolver."""
    for (slug, (bits, pattern, _defaults)) in resolver.reverse_dict.iteritems():
        if not isinstance(slug, basestring):
            continue

        if namespace:
            slug = "{}:{}".format(namespace, slug)

        (template, args) = bits[0]
        data = (prefix + template,
                args,
                prefix + strip_names(pattern))

        yield (slug, data)


class Command(BaseCommand):

    args = '<install>'
    option_list = BaseCommand.option_list + (
        make_option(
            '--namespace',
            action='append',
            dest='namespaces',
            help="Include urls from the specified namespace(s)",
        ),
        make_option(
            '--all-namespaces',
            action='store_true',
            default=False,
            help="Include urls from all namespaces",
        ),
        make_option(
            '--exclude',
            action='append',
            dest='excludes',
            help="Exclude urls matching the given regular expression(s)",
        ),
        make_option(
            '--include',
            action='append',
            dest='includes',
            help="Include only urls matching the given regular expression(s)",
        ),
        # TODO:
        #make_option('--minify', action='store_true', default=False,
        #            help="..."),
    )

    def handle(self, command=None, **options):
        if command and command not in ('install',):
            raise CommandError("unsupported command: {}".format(command))
        install = command == 'install'
        install_path = getattr(settings, 'JSURLS_INSTALL_PATH', None)
        if install and not install_path:
            raise CommandError("cannot install: JSURLS_INSTALL_PATH is not set")

        if options['namespaces'] and options['all_namespaces']:
            raise CommandError("incompatible options: --namespace and --all-namespaces")

        includes = [re.compile(include) for include in options['includes'] or ()]
        excludes = [re.compile(exclude) for exclude in options['excludes'] or ()]

        resolver = urlresolvers.get_resolver(None)

        if options['all_namespaces']:
            namespaces = resolver.namespace_dict.keys()
        else:
            namespaces = options['namespaces'] or []

        paths = generate_reversals(resolver)
        for namespace in namespaces:
            (prefix, ns_resolver) = resolver.namespace_dict[namespace]
            paths = chain(paths, generate_reversals(ns_resolver, namespace, prefix))

        paths_filtered = {
            slug: (template, args, pattern)
            for (slug, (template, args, pattern)) in paths
            if all(include.search(template) for include in includes) and
               not any(exclude.search(template) for exclude in excludes)
        }
        paths_encoded = json.dumps(paths_filtered, indent=4)

        javascript = render_to_string('jsurls/router.js', {
            'namespace': getattr(settings, 'JSURLS_NAMESPACE', None),
            # add additional 4-space indent for easy reading default block code:
            'paths': paths_encoded.replace('\n', '\n    '),
        })

        if install:
            raise NotImplementedError # TODO
        else:
            sys.stdout.write(javascript)
