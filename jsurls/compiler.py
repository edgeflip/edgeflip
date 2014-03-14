import itertools
import json
import re

from django.core import urlresolvers
from django.template.loader import render_to_string
from django.utils import datastructures
from rjsmin import jsmin


All = object()

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

        yield (
            slug,
            prefix + template,
            args,
            prefix + strip_names(pattern),
        )


def compile_lookup(urlconf=None, namespaces=(), includes=(), excludes=()):
    """Compile a dictionary mapping URL path names to patterns in the given
    urlconf (defaulting to root).

    Namespaced URLs are not included unless specified. All namespaces are
    included when `All` is given.

    URLs may be filtered by specifying `includes` and/or `excludes` as
    sequences of regular expressions.

    """
    resolver = urlresolvers.get_resolver(None)

    if namespaces == All:
        namespaces = resolver.namespace_dict.keys()

    includes = {re.compile(include) for include in includes}
    excludes = {re.compile(exclude) for exclude in excludes}

    paths = generate_reversals(resolver)
    for namespace in namespaces:
        (prefix, ns_resolver) = resolver.namespace_dict[namespace]
        paths = itertools.chain(paths, generate_reversals(ns_resolver, namespace, prefix))

    return datastructures.SortedDict(
        (slug, (template, args, pattern))
        for (slug, template, args, pattern) in paths
        if (
            all(include.search(template) for include in includes) and
            not any(exclude.search(template) for exclude in excludes)
        )
    )


def render_js(paths, js_namespace=None, minify=False, template_name='jsurls/router.js'):
    """Render the JavaScript library template with the given URL path lookup
    dictionary.

    """
    paths_encoded = json.dumps(paths, indent=4)
    javascript = render_to_string(template_name, {
        'namespace': js_namespace,
        # add additional 4-space indent for easy reading default block code:
        'paths': paths_encoded.replace('\n', '\n    '),
    })
    if minify:
        return jsmin(javascript)
    return javascript
