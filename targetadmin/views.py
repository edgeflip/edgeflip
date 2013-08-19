from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse

from targetadmin.utils import internal
from targetadmin import forms
from targetshare.models import relational


@internal
def edit_client(request, client_pk=None):
    """ Simple view for creating new clients """
    if client_pk:
        client = get_object_or_404(relational.Client, pk=client_pk)
        form = forms.ClientForm(instance=client)
    else:
        client = None
        form = forms.ClientForm()

    if request.method == 'POST':
        form = forms.ClientForm(instance=client, data=request.POST)
        if form.is_valid():
            obj = form.save()
            return redirect(reverse('client-detail', args=[obj.pk]))

    return render(request, 'targetadmin/client_edit.html', {
        'form': form,
        'client': client
    })
