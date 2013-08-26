from django.shortcuts import get_object_or_404, redirect, render

from targetadmin.utils import internal
from targetadmin import forms
from targetshare.models import relational
from targetadmin.views.base import (
    ClientRelationListView,
    ClientRelationDetailView,
)


class CampaignListView(ClientRelationListView):
    model = relational.Campaign
    object_string = 'Campaign'
    detail_url_name = 'campaign-detail'
    create_url_name = 'campaign-new'


campaign_list = internal(CampaignListView.as_view())


class CampaignDetailView(ClientRelationDetailView):
    model = relational.Campaign
    object_string = 'Campaign'
    edit_url_name = 'campaign-edit'
    template_name = 'targetadmin/campaign_detail.html'


campaign_detail = internal(CampaignDetailView.as_view())


@internal
def campaign_create(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    form = forms.CampaignForm(client=client)
    if request.method == 'POST':
        form = forms.CampaignForm(
            client=client, data=request.POST)
        if form.is_valid():
            campaign = form.save()
            return redirect('campaign-detail', client.pk, campaign.pk)

    return render(request, 'targetadmin/campaign_edit.html', {
        'client': client,
        'form': form
    })
