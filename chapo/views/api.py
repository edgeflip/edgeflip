"""Views providing protected API methods to authorized consumers."""
import enum
import json
import urllib

from django import forms
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, QueryDict
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from core.utils.http import DjangoJsonHttpResponse
from core.utils.decorators import ViewDecorator

from chapo.models import ShortenedUrl, EFApiKey


class require_api_key(ViewDecorator):

    # Assume that API methods which require an authentication header in every
    # request, though imperfect, are not susceptible to CSRF attacks:
    csrf_exempt = True

    def __call__(self, request, *args, **kws):
        authorization = request.META.get('HTTP_AUTHORIZATION', '')
        if authorization.lower().startswith('apikey '):
            try:
                (_auth_type, data) = authorization.split()
                (user_name, api_key) = data.split(':', 1)
            except ValueError:
                pass
            else:
                if EFApiKey.objects.filter(
                    ef_app='chapo',
                    ef_api_user=user_name,
                    key=api_key,
                ).exists():
                    return self._view(request, *args, **kws)

        return HttpResponse('Unauthorized', status=401)


@enum.unique
class ContentTypes(str, enum.Enum):

    JSON = 'application/json'
    URLENC = 'application/x-www-form-urlencoded'

    def __str__(self):
        return self.value


def serialize(shortened):
    return [
        ('slug', shortened.slug),
        ('url', shortened.url),
        ('event_type', shortened.event_type),
        ('description', shortened.description),
        ('campaign', shortened.campaign_id),
        ('created', shortened.created),
        ('updated', shortened.updated),
    ]


@require_api_key
@require_http_methods(['GET'])
def dump_slug(request, slug, extension):
    try:
        content_type = ContentTypes[extension.upper()]
    except KeyError:
        pass
    else:
        shortened = get_object_or_404(ShortenedUrl, slug=slug)
        serialized = serialize(shortened)

        if content_type is ContentTypes.JSON:
            return DjangoJsonHttpResponse(dict(serialized), separators=(',', ':'))
        elif content_type is ContentTypes.URLENC:
            encoded = urllib.urlencode([
                (key, '' if value is None else value)
                for (key, value) in serialized
            ])
            return HttpResponse(encoded, content_type=content_type)

    raise Http404


class ShortenedUrlApiForm(forms.ModelForm):

    class Meta(object):
        model = ShortenedUrl
        fields = ('slug', 'url', 'event_type', 'description', 'campaign')

    def __init__(self, *args, **kws):
        super(ShortenedUrlApiForm, self).__init__(*args, **kws)
        defaults = self._get_defaults()
        self._merge_defaults(defaults)

    def _get_defaults(self):
        """Merge the form's various "initial" values into a single dict of "defaults".

        As these values come either from model field defaults or an existing
        model instance, and as we're only using the form for validation, the
        existing feature of "initial" values does not make sense. We don't
        provide the form with initial values filled in, to be written over;
        rather, an API user, knowing the interface, sends data, in a single
        request; and, we'll fill in the defaults. (See also: `_merge_defaults`.)

        """
        field_initials = (
            (name, (field.initial() if callable(field.initial) else field.initial))
            for (name, field) in self.fields.iteritems()
        )
        return dict(field_initials, **self.initial)

    def _merge_defaults(self, defaults):
        """Merge a dict of form "defaults" into the request's data dict."""
        for (name, value) in defaults.iteritems():
            if name in self.data:
                continue

            self.data[name] = value


def _shorten(request, slug=None):
    """Generic request handler for all requests to create or update a redirect."""
    content_type = request.META.get('CONTENT_TYPE', '')
    try:
        if content_type == ContentTypes.JSON:
            data = json.load(request)
        elif content_type == ContentTypes.URLENC:
            if request.method == 'POST':
                data = request.POST.copy()
            else:
                data = QueryDict(request.body, mutable=True)
        else:
            return HttpResponse(
                ('Unknown Content-Type. Try one of: ' +
                ', '.join(str(content_type) for content_type in ContentTypes)),
                status=415,
            )
    except ValueError:
        return HttpResponse(
            "No object compatible with {} could be decoded".format(content_type),
            status=400,
        )

    if slug is None:
        # No slug provided in URL (this is a POST); we'll create one.
        shortened = None
    else:
        # Check for update
        try:
            shortened = ShortenedUrl.objects.get(slug=slug)
        except ShortenedUrl.DoesNotExist:
            # Slug provided in URL is novel; we'll use it.
            shortened = None
            data['slug'] = slug

    form = ShortenedUrlApiForm(data, instance=shortened)
    if form.is_valid():
        result = form.save()
        response = HttpResponse(status=(201 if shortened is None else 204))
        response['Location'] = reverse('chapo:main', args=[result.slug])
        return response

    if content_type == ContentTypes.JSON:
        return DjangoJsonHttpResponse(form.errors, separators=(',', ':'), status=400)
    elif content_type == ContentTypes.URLENC:
        # urllib is *not* cool about Django's custom error collections:
        errors = [(key, list(errlist)) for (key, errlist) in form.errors.items()]
        encoded = urllib.urlencode(errors, doseq=True)
        return HttpResponse(encoded, content_type=content_type, status=400)


@require_api_key
@require_http_methods(['PUT'])
def upsert_slug(request, slug): # routed via urls.main()
    return _shorten(request, slug)


@require_api_key
@require_http_methods(['POST'])
def shorten_url(request):
    return _shorten(request)
