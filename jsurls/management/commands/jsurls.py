from __future__ import absolute_import

import os.path
import sys
from optparse import make_option

from django.core.management import BaseCommand, CommandError
from six.moves import input

from jsurls import compiler
from jsurls.conf import settings


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
            default=list(settings.URL_NAMESPACES),
            metavar='NAMESPACE',
            help="Include urls from the specified project namespace(s) "
                 "(default: {})".format(settings.URL_NAMESPACES),
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
            default=list(settings.URL_EXCLUDES),
            metavar='EXPRESSION',
            help="Exclude urls matching the given regular expression(s) "
                 "(default filters: {})".format(settings.URL_EXCLUDES),
        ),
        make_option(
            '--include',
            action='append',
            dest='includes',
            default=list(settings.URL_INCLUDES),
            metavar='EXPRESSION',
            help="Include only urls matching the given regular expression(s) "
                 "(default filters: {})".format(settings.URL_INCLUDES),
        ),
        make_option(
            '--js-namespace',
            default=settings.JS_NAMESPACE,
            help='JavaScript namespace under which to write the router (default: "{}")'
                 .format(settings.JS_NAMESPACE),
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
        if install and not settings.INSTALL_PATH:
            raise CommandError("cannot install: JSURLS_INSTALL_PATH is not set")

        namespaces = set(options['namespaces'] or ())
        if options['all_namespaces']:
            if namespaces.difference(settings.URL_NAMESPACES):
                raise CommandError("incompatible options: --namespace and --all-namespaces")
            else:
                namespaces = compiler.All

        paths = compiler.compile_lookup(
            namespaces=namespaces,
            includes=(options['includes'] or ()),
            excludes=(options['excludes'] or ()),
        )
        javascript = compiler.render_js(
            paths,
            options['js_namespace'],
            options['minify'],
        )

        if install:
            if options['interactive'] and os.path.exists(settings.INSTALL_PATH):
                self.stdout.write("Will OVERWRITE compiled url router to:")
                self.stdout.write("    `{}'".format(settings.INSTALL_PATH))
                self.stdout.write("(To write to stdout, do not specify the 'install' command.)")
                confirm = ''
                while confirm not in ('yes', 'no'):
                    confirm = input("Type 'yes' to continue, or 'no' to cancel: ").lower()
                if confirm == 'no':
                    self.stdout.write("Installation cancelled")
                    return

            out = open(settings.INSTALL_PATH, 'wb')
        else:
            out = sys.stdout

        out.write(javascript)
