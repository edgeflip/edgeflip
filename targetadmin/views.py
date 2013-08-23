from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.forms.models import modelformset_factory

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


class FilterObjectListView(ClientRelationListView):
    model = relational.Filter
    object_string = 'Filter'
    detail_url_name = 'filter-detail'
    create_url_name = 'filter-new'


filter_list = internal(FilterObjectListView.as_view())


class FilterObjectDetailView(ClientRelationDetailView):
    model = relational.Filter
    object_string = 'Filter'
    edit_url_name = 'filter-edit'
    template_name = 'targetadmin/filter_detail.html'


filter_detail = internal(FilterObjectDetailView.as_view())


class FilterFormView(ClientRelationFormView):
    form_class = forms.FilterForm
    model = relational.Filter
    queryset = relational.Filter.objects.all()
    success_url = 'filter-detail'
    object_string = 'Filter'


filter_new = internal(FilterFormView.as_view())


def filter_edit(request, client_pk, pk):
    """ Creates a filter set """
    client = get_object_or_404(relational.Client, pk=client_pk)
    filter_obj = get_object_or_404(relational.Filter, pk=pk)
    filter_form = forms.FilterForm(instance=filter_obj)
    extra_forms = 2
    ff_set = modelformset_factory(
        relational.FilterFeature,
        extra=extra_forms
    )
    formset = ff_set(
        queryset=relational.FilterFeature.objects.filter(filter=filter_obj),
        initial=[{'filter': filter_obj} for x in range(extra_forms)]
    )
    if request.method == 'POST':
        filter_form = forms.FilterForm(data=request.POST, instance=filter_obj)
        formset = ff_set(
            data=request.POST,
            queryset=relational.FilterFeature.objects.filter(filter=filter_obj)
        )
        valid_formset = formset.is_valid()
        valid_forms = []
        if valid_formset:
            valid_forms = formset.forms
        else:
            # Let's make sure our initial data isn't the cause of this
            valid_formset = True
            for form in formset.forms:
                if form.is_valid():
                    valid_forms.append(form)
                else:
                    if form._changed_data != ['filter']:
                        valid_formset = False
        if valid_formset and filter_form.is_valid():
            for form in valid_forms:
                form.save()
            filter_form.save()
            return redirect('filter-detail', client.pk, filter_obj.pk)

    return render(request, 'targetadmin/filter_edit.html', {
        'client': client,
        'filter_obj': filter_obj,
        'formset': formset,
        'filter_form': filter_form,
    })


class ChoiceSetListView(ClientRelationListView):
    model = relational.ChoiceSet
    object_string = 'Choice Set'
    detail_url_name = 'cs-detail'
    create_url_name = 'cs-new'


cs_list = internal(ChoiceSetListView.as_view())


class ChoiceSetDetailView(ClientRelationDetailView):
    model = relational.ChoiceSet
    object_string = 'Choice Set'
    edit_url_name = 'cs-edit'
    template_name = 'targetadmin/cs_detail.html'


cs_detail = internal(ChoiceSetDetailView.as_view())


class ChoiceSetFormView(ClientRelationFormView):
    form_class = forms.ChoiceSetForm
    model = relational.ChoiceSet
    queryset = relational.ChoiceSet.objects.all()
    success_url = 'cs-detail'
    object_string = 'Choice Set'


cs_new = internal(ChoiceSetFormView.as_view())


def cs_edit(request, client_pk, pk):
    ''' Choice Set Editing View '''
    client = get_object_or_404(relational.Client, pk=client_pk)
    cs = get_object_or_404(relational.ChoiceSet, pk=pk)
    cs_form = forms.ChoiceSetForm(instance=cs)
    extra_forms = 2
    cs_set = modelformset_factory(
        relational.ChoiceSetFilter,
        extra=extra_forms
    )
    formset = cs_set(
        queryset=relational.ChoiceSetFilter.objects.filter(choice_set=cs),
        initial=[{'choice_set': cs} for x in range(extra_forms)]
    )
    if request.method == 'POST':
        cs_form = forms.ChoiceSetForm(data=request.POST, instance=cs)
        formset = cs_set(
            data=request.POST,
            queryset=relational.ChoiceSetFilter.objects.filter(choice_set=cs)
        )
        valid_formset = formset.is_valid()
        valid_forms = []
        if valid_formset:
            valid_forms = formset.forms
        else:
            # Let's make sure our initial data isn't the cause of this
            valid_formset = True
            for form in formset.forms:
                if form.is_valid():
                    valid_forms.append(form)
                else:
                    if form._changed_data != ['choice_set']:
                        valid_formset = False
        if valid_formset and cs_form.is_valid():
            for form in valid_forms:
                form.save()
            cs_form.save()
            return redirect('cs-detail', client.pk, cs.pk)

    return render(request, 'targetadmin/cs_edit.html', {
        'client': client,
        'choice_set': cs,
        'formset': formset,
        'cs_form': cs_form,
    })


class ButtonListView(ClientRelationListView):
    model = relational.ButtonStyle
    object_string = 'Button Style'
    detail_url_name = 'button-detail'
    create_url_name = 'button-new'


button_list = internal(ButtonListView.as_view())


class ButtonDetailView(ClientRelationDetailView):
    model = relational.ButtonStyle
    object_string = 'Button Style'
    edit_url_name = 'button-edit'


button_detail = internal(ButtonDetailView.as_view())


class ButtonFormView(ClientRelationFormView):
    form_class = forms.ButtonStyleForm
    model = relational.ButtonStyle
    queryset = relational.ButtonStyle.objects.all()
    success_url = 'button-detail'
    object_string = 'Button Style'

    def get_form(self, form_class):
        form_kwargs = self.get_form_kwargs()
        if self.object:
            form_kwargs['instance'] = self.object.buttonstylefiles.get()
            form_kwargs['initial'] = {
                'name': self.object.name,
                'description': self.object.description,
                'client': self.object.client
            }
        else:
            form_kwargs['client'] = self.client
        return form_class(**form_kwargs)


button_edit = internal(ButtonFormView.as_view())
