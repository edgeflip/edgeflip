import json
import os.path
import re
import sys
from itertools import chain
from optparse import make_option

from django.conf import settings
from django.core import urlresolvers
from django.core.management import BaseCommand, CommandError
from django.template.loader import render_to_string
from rjsmin import jsmin
from six.moves import input


GROUP_NAME_PATTERN = re.compile(r'\?P<[^>]+>')

# Options from Django settings:
INSTALL_PATH = getattr(settings, 'JSURLS_INSTALL_PATH', None)
JS_NAMESPACE = getattr(settings, 'JSURLS_JS_NAMESPACE', 'router')
URL_INCLUDES = list(getattr(settings, 'JSURLS_URL_INCLUDES', ()))
URL_EXCLUDES = list(getattr(settings, 'JSURLS_URL_EXCLUDES', ()))
URL_NAMESPACES = list(getattr(settings, 'JSURLS_URL_NAMESPACES', ()))


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
    help = (
        "Compiles a JavaScript URL path reversal library for the project based "
        "on its urlconf.\n\n"
        "Output is written by default to stdout, and may be redirected as needed. "
        "Alternatively, an installation path may be managed within Django "
        "settings (JSURLS_INSTALL_PATH), and output written to this path via the "
        '"install" command.'
    )
    option_list = BaseCommand.option_list + (
        make_option(
            '--noinput',
            action='store_false',
            dest='interactive',
            default=True,
            help='Tells Django to NOT prompt the user for input of any kind.',
        ),
        make_option(
            '--namespace',
            action='append',
            dest='namespaces',
            default=URL_NAMESPACES,
            metavar='NAMESPACE',
            help="Include urls from the specified project namespace(s) "
                 "(default: {})".format(URL_NAMESPACES),
        ),
        make_option(
            '--all-namespaces',
            action='store_true',
            default=False,
            help="Include urls from all project namespaces",
        ),
        make_option(
            '--exclude',
            action='append',
            dest='excludes',
            default=URL_EXCLUDES,
            metavar='EXPRESSION',
            help="Exclude urls matching the given regular expression(s) "
                 "(default filters: {})".format(URL_EXCLUDES),
        ),
        make_option(
            '--include',
            action='append',
            dest='includes',
            default=URL_INCLUDES,
            metavar='EXPRESSION',
            help="Include only urls matching the given regular expression(s) "
                 "(default filters: {})".format(URL_INCLUDES),
        ),
        make_option(
            '--js-namespace',
            default=JS_NAMESPACE,
            help='JavaScript namespace under which to write the router (default: "{}")'
                 .format(JS_NAMESPACE),
        ),
        make_option(
            '--minify',
            action='store_true',
            default=False,
            help="Minify JavaScript output",
        ),
    )

    def handle(self, command=None, **options):
        if command and command not in ('install',):
            raise CommandError("unsupported command: {}".format(command))
        install = command == 'install'
        if install and not INSTALL_PATH:
            raise CommandError("cannot install: JSURLS_INSTALL_PATH is not set")

        namespaces = set(options['namespaces'] or ())
        if options['all_namespaces'] and namespaces.difference(URL_NAMESPACES):
            raise CommandError("incompatible options: --namespace and --all-namespaces")

        includes = {re.compile(include) for include in options['includes'] or ()}
        excludes = {re.compile(exclude) for exclude in options['excludes'] or ()}

        resolver = urlresolvers.get_resolver(None)

        if options['all_namespaces']:
            namespaces = resolver.namespace_dict.keys()

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
            'namespace': options['js_namespace'],
            # add additional 4-space indent for easy reading default block code:
            'paths': paths_encoded.replace('\n', '\n    '),
        })
        if options['minify']:
            javascript = jsmin(javascript)

        if install:
            if options['interactive'] and os.path.exists(INSTALL_PATH):
                self.stdout.write("Will OVERWRITE compiled url router to:")
                self.stdout.write("    `{}'".format(INSTALL_PATH))
                self.stdout.write("(To write to stdout, do not specify the 'install' command.)")
                confirm = ''
                while confirm not in ('yes', 'no'):
                    confirm = input("Type 'yes' to continue, or 'no' to cancel: ").lower()
                if confirm == 'no':
                    self.stdout.write("Installation cancelled")
                    return

            out = open(INSTALL_PATH, 'wb')
        else:
            out = sys.stdout

        out.write(javascript)
