from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404

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
        self.object = self.get_object() if self.kwargs.get(self.pk_url_kwarg) else None
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


class ClientRelationListView(ListView):
    """ Simple extension of ListView to inject Client objects into the
    context and to filter the queryset down by objects that match the client
    specified.
    """
    object_string = None
    template_name = 'targetadmin/client_relation_list.html'
    detail_url_name = None
    create_url_name = None

    def get_queryset(self):
        queryset = super(ClientRelationListView, self).get_queryset()
        return queryset.filter(client=self.client)

    def get_context_data(self, **kwargs):
        context = super(ClientRelationListView, self).get_context_data(**kwargs)
        context.update({
            'client': self.client,
            'obj_str': self.object_string,
            'detail_url_name': self.detail_url_name,
            'create_url_name': self.create_url_name
        })
        return context

    def get(self, request, *args, **kwargs):
        self.client = get_object_or_404(
            relational.Client,
            pk=self.kwargs.get('client_pk')
        )
        return super(ClientRelationListView, self).get(request, *args, **kwargs)


class ClientRelationDetailView(DetailView):
    """ Simple extension of DetailView to basically assist in namespacing
    various objects by their relation to a specific Client
    """
    object_string = None
    template_name = 'targetadmin/client_relation_detail.html'
    edit_url_name = None

    def get_context_data(self, **kwargs):
        context = super(ClientRelationDetailView, self).get_context_data(**kwargs)
        context.update({
            'client': self.client,
            'obj_str': self.object_string,
            'edit_url_name': self.edit_url_name
        })
        return context

    def get_object(self, queryset=None):
        obj = super(ClientRelationDetailView, self).get_object(queryset=queryset)
        if obj.client != self.client:
            raise Http404('Invalid Client')
        return obj

    def get(self, request, *args, **kwargs):
        self.client = get_object_or_404(
            relational.Client,
            pk=self.kwargs.get('client_pk')
        )
        return super(ClientRelationDetailView, self).get(request, *args, **kwargs)


class ClientRelationFormView(CRUDView):
    object_string = None
    template_name = 'targetadmin/client_relation_edit.html'

    def dispatch(self, request, *args, **kwargs):
        self.client = get_object_or_404(
            relational.Client,
            pk=self.kwargs.get('client_pk')
        )
        return super(ClientRelationFormView, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class):
        form_kwargs = self.get_form_kwargs()
        if self.object:
            form_kwargs['instance'] = self.object
        else:
            form_kwargs['instance'] = self.model(client=self.client)
        return form_class(**form_kwargs)

    def get_context_data(self, **kwargs):
        context = super(ClientRelationFormView, self).get_context_data(**kwargs)
        context['client'] = self.client
        context['obj_str'] = self.object_string
        return context

    def get_success_url(self):
        if self.success_url:
            return reverse(
                self.success_url,
                args=[self.client.pk, self.object.pk]
            )
        else:
            raise ImproperlyConfigured(
                'No URL to redirect to. Provide a success_url.')


class ContentListView(ClientRelationListView):
    model = relational.ClientContent
    object_string = 'Content'
    detail_url_name = 'content-detail'
    create_url_name = 'content-new'


content_list = internal(ContentListView.as_view())


class ContentDetailView(ClientRelationDetailView):
    model = relational.ClientContent
    object_string = 'Content'
    edit_url_name = 'content-edit'


content_detail = internal(ContentDetailView.as_view())


class ContentFormView(ClientRelationFormView):
    form_class = forms.ContentForm
    model = relational.ClientContent
    queryset = relational.ClientContent.objects.all()
    success_url = 'content-detail'
    object_string = 'Content'


content_edit = internal(ContentFormView.as_view())


class FBObjectListView(ClientRelationListView):
    model = relational.FBObject
    object_string = 'Facebook Object'
    detail_url_name = 'fb-obj-detail'
    create_url_name = 'fb-obj-new'


fb_object_list = internal(FBObjectListView.as_view())


class FBObjectDetailView(ClientRelationDetailView):
    model = relational.FBObject
    object_string = 'Facebook Object'
    edit_url_name = 'fb-obj-edit'


fb_object_detail = internal(FBObjectDetailView.as_view())


class FBObjectFormView(ClientRelationFormView):
    form_class = forms.FBObjectAttributeForm
    model = relational.FBObject
    queryset = relational.FBObject.objects.all()
    success_url = 'fb-obj-detail'
    object_string = 'Facebook Object'

    def get_form(self, form_class):
        form_kwargs = self.get_form_kwargs()
        if self.object:
            form_kwargs['instance'] = self.object.fbobjectattribute_set.get()
            form_kwargs['initial'] = {
                'name': self.object.name,
                'description': self.object.description,
                'client': self.object.client
            }
        else:
            form_kwargs['client'] = self.client
        return form_class(**form_kwargs)


fb_object_edit = internal(FBObjectFormView.as_view())
