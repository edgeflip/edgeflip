from django.shortcuts import get_object_or_404, redirect, render
from django.forms.models import modelformset_factory

from targetadmin.utils import internal
from targetadmin import forms
from targetshare.models import relational
from targetadmin.views.base import (
    ClientRelationListView,
    ClientRelationDetailView,
    ClientRelationFormView
)


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
    template_name = 'targetadmin/filter_create.html'


filter_new = internal(FilterFormView.as_view())


def filter_edit(request, client_pk, pk):
    """ Creates a filter set """
    client = get_object_or_404(relational.Client, pk=client_pk)
    filter_obj = get_object_or_404(relational.Filter, pk=pk)
    filter_form = forms.FilterForm(instance=filter_obj)
    extra_forms = 2
    ff_set = modelformset_factory(
        relational.FilterFeature,
        extra=extra_forms,
        exclude=('end_dt', 'value_type')
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

        # Filter Features are inherently nully things, but we know we should
        # expect at least a value back from the form.
        formset.is_valid()
        filled_forms = [x for x in formset.forms if x.cleaned_data.get('value')]
        valid_formset = True
        for form in filled_forms:
            if not form.is_valid() and form._changed_data != ['filter']:
                valid_formset = False

        if valid_formset and filter_form.is_valid():
            for form in filled_forms:
                form.save()
            filter_form.save()
            return redirect('filter-detail', client.pk, filter_obj.pk)

    return render(request, 'targetadmin/filter_edit.html', {
        'client': client,
        'filter_obj': filter_obj,
        'formset': formset,
        'filter_form': filter_form,
    })
