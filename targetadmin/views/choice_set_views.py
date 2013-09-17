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

    def csf_field_callback(f, **kwargs):
        ''' Callback method for modelformset_factory to leverage and ask us for
        the form field that should be used for various model fields. Using it here
        to filter down the filters in a choice set filter object by client
        '''
        if f.name == 'filter':
            return forms.forms.ModelChoiceField(
                queryset=relational.Filter.objects.filter(
                    client=client
                )
            )
        else:
            return f.formfield(**kwargs)

    cs_set = modelformset_factory(
        relational.ChoiceSetFilter,
        extra=extra_forms,
        exclude=('end_dt', 'propensity_model_type'),
        formfield_callback=csf_field_callback
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
        formset.is_valid()
        filled_forms = [x for x in formset.forms if x.cleaned_data.get('filter')]
        valid_formset = True
        for form in filled_forms:
            if not form.is_valid() and form._changed_data != ['choice_set']:
                valid_formset = False

        if valid_formset and cs_form.is_valid():
            for form in filled_forms:
                form.save()
            cs_form.save()
            return redirect('cs-detail', client.pk, cs.pk)

    return render(request, 'targetadmin/cs_edit.html', {
        'client': client,
        'choice_set': cs,
        'formset': formset,
        'cs_form': cs_form,
    })
