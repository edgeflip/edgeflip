from __future__ import absolute_import

import os.path
import sys
from optparse import make_option

from django.core.management import BaseCommand, CommandError
from django.utils import text
from six.moves import input

from jsurls import compiler
from jsurls.conf import Profile, settings
from jsurls.structs import All


GLOBAL_KEYS = ('namespace', 'include', 'exclude', 'js-namespace')

NON_PROFILE_OPTIONS = ('all-namespaces',) + GLOBAL_KEYS

URL_NAMESPACES = list(settings.URL_NAMESPACES)
URL_EXCLUDES = list(settings.URL_EXCLUDES)
URL_INCLUDES = list(settings.URL_INCLUDES)


def specified_key(name):
    head = '--' + name + '='
    return any(arg.startswith(head) for arg in sys.argv[2:])


def pmsg(name, msg):
    return msg if name is None else "[{}] {}".format(name, msg)


class Command(BaseCommand):

    INSTALL = 'install'
    DUMP = 'dump'
    commands = (DUMP, INSTALL)

    args = '<{{{}}} [PROFILE, ...]>'.format('|'.join(commands))
    help = (
        "Compiles a JavaScript URL path reversal library for the project based "
        "on its urlconf."
        "\n\n"
        "Output is written by default to stdout (dump), and may be redirected as needed.\n"
        "Alternatively, an installation path may be managed within Django "
        "settings (JSURLS_INSTALL_PATH), and output written to this path (install)."
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
            default=settings.JS_NAMESPACE,
            metavar="VARNAME",
            help='JavaScript namespace under which to write the router (default: "{}")'
                 .format(settings.JS_NAMESPACE),
        ),
        make_option(
            '--minify',
            action='store_true',
            default=False,
            help="Minify JavaScript output",
        ),
        make_option(
            '--all-profiles',
            action='store_true',
            default=False,
            help="Compile JavaScript for all profiles",
        ),
    )

    def __init__(self):
        super(Command, self).__init__()
        self.install = self.minify = self.interactive = self.verbosity = None

    def pout(self, name, msg, verbosity=0):
        if self.verbosity >= verbosity:
            self.stdout.write(pmsg(name, msg))

    def perr(self, name, msg, verbosity=0):
        if self.verbosity >= verbosity:
            self.stderr.write(pmsg(name, msg))

    def handle(self, command=None, *profile_names, **options):
        if command and command not in self.commands:
            raise CommandError("unsupported command: {}".format(command))

        if options['all_profiles'] and profile_names:
            raise CommandError('option "all-profiles" incompatible with named profiles')

        self.install = command == self.INSTALL
        self.minify = options['minify']
        self.interactive = options['interactive']
        self.verbosity = int(options['verbosity'])

        if options['all_profiles'] or profile_names:
            if options['all_namespaces'] or any(specified_key(key) for key in GLOBAL_KEYS):
                raise CommandError(
                    "the following options are incompatible with profiles: {}"
                    .format(text.get_text_list(NON_PROFILE_OPTIONS, 'and'))
                )

            if options['all_profiles']:
                profiles = settings.PROFILES.items()
            else:
                try:
                    profiles = [(profile_name, settings.PROFILES[profile_name])
                                for profile_name in profile_names]
                except KeyError as exc:
                    raise CommandError("no such profile: {}".format(exc))

        else:
            if options['all_namespaces']:
                if specified_key('namespace'):
                    raise CommandError('incompatible options: "namespace" and "all-namespaces"')
                else:
                    namespaces = All
            else:
                namespaces = set(options['namespaces'] or ())

            profiles = [(None,
                         Profile(URL_NAMESPACES=namespaces,
                                 URL_INCLUDES=(options['includes'] or ()),
                                 URL_EXCLUDES=(options['excludes'] or ()),
                                 JS_NAMESPACE=options['js_namespace'],
                                 INSTALL_PATH=settings.INSTALL_PATH))]

        if self.install:
            for (profile_name, profile) in profiles:
                if not profile.INSTALL_PATH:
                    raise CommandError(pmsg(profile_name, "cannot install: JSURLS_INSTALL_PATH is not set"))

        for (profile_name, profile) in profiles:
            self.handle_profile(profile_name, profile)

    def handle_profile(self, name, profile):
        paths = compiler.compile_lookup(
            namespaces=profile.URL_NAMESPACES,
            includes=profile.URL_INCLUDES,
            excludes=profile.URL_EXCLUDES,
        )
        javascript = compiler.render_js(paths, profile.JS_NAMESPACE, self.minify)

        if self.install:
            if self.interactive and os.path.exists(profile.INSTALL_PATH):
                self.pout(name, "Will OVERWRITE compiled url router to:")
                self.pout(name, "    `{}'".format(profile.INSTALL_PATH))
                self.pout(name, "(To write to stdout, do not specify the 'install' command.)", 1)

                confirm = ''
                while confirm not in ('yes', 'no'):
                    confirm = input("Type 'yes' to continue, or 'no' to cancel: ").lower()

                if confirm == 'no':
                    self.perr(name, "installation cancelled", 1)
                    return

            out = open(profile.INSTALL_PATH, 'wb')
        else:
            out = sys.stdout

        out.write(javascript)
