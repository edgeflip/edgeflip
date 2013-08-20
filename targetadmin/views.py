from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured

from targetadmin.utils import internal
from targetadmin import forms
from targetshare.models import relational


class CRUDView(UpdateView):
    """ Generic Class Based View which handles creating and updating Model
    objects. The Django built in views handle updating OR creating, while
    this should be able to handle both.

    Required class level attributes:

        template_name: Template to render to
        form_class: Form class to leverage
        success_url: Name of URL to reverse after a form save
        success_object: Bool, determines if we should redirect on save to a
            specific object URL. Set this to False if you want to send someone
            to a non-distinct URL, such as a landing page like /clients/.
        queryset: Queryset to use when retrieving an existing object for edit

    """
    template_name = None
    form_class = None
    success_url = None
    success_object = True
    queryset = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object() if self.kwargs.get(self.pk_url_kwarg) else None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() if self.kwargs else None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        return super(CRUDView, self).form_valid(form)

    def get_success_url(self):
        if self.success_url:
            return reverse(
                self.success_url,
                args=[self.object.pk if self.success_object else None]
            )
        else:
            raise ImproperlyConfigured(
                'No URL to redirect to. Provide a success_url.')


class ClientFormView(CRUDView):
    template_name = 'targetadmin/client_edit.html'
    form_class = forms.ClientForm
    success_url = 'client-detail'
    queryset = relational.Client.objects.all()

client_view = internal(ClientFormView.as_view())


class ContentListView(ListView):
    model = relational.ClientContent
    template_name = 'targetadmin/content_list.html'

    def get_context_data(self, **kwargs):
        context = super(ContentListView, self).get_context_data(**kwargs)
        context['client'] = get_object_or_404(
            relational.Client,
            pk=self.kwargs.get('client_pk')
        )
        return context

content_list = internal(ContentListView.as_view())


class ContentDetailView(DetailView):
    model = relational.ClientContent
    template_name = 'targetadmin/content_detail.html'

    def get_context_data(self, **kwargs):
        context = super(ContentDetailView, self).get_context_data(**kwargs)
        context['client'] = get_object_or_404(
            relational.Client,
            pk=self.kwargs.get('client_pk')
        )
        return context

content_detail = internal(ContentDetailView.as_view())


class ContentFormView(CRUDView):
    template_name = 'targetadmin/content_edit.html'
    form_class = forms.ContentForm
    model = relational.ClientContent
    queryset = relational.ClientContent.objects.all()
    success_url = 'content-detail'

    def dispatch(self, request, *args, **kwargs):
        self.client = relational.Client.objects.get(pk=kwargs['client_pk'])
        return super(ContentFormView, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class):
        form_kwargs = self.get_form_kwargs()
        if self.object:
            form_kwargs['instance'] = self.object
        else:
            form_kwargs['instance'] = relational.ClientContent(
                client=self.client)
        return form_class(**form_kwargs)

    def get_context_data(self, **kwargs):
        context = super(ContentFormView, self).get_context_data(**kwargs)
        context['client'] = self.client
        return context

content_edit = internal(ContentFormView.as_view())
