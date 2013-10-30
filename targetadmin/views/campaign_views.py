from django.shortcuts import get_object_or_404, redirect, render

from targetadmin import utils
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


campaign_list = CampaignListView.as_view()


class CampaignDetailView(ClientRelationDetailView):
    model = relational.Campaign
    object_string = 'Campaign'
    edit_url_name = 'campaign-edit'
    template_name = 'targetadmin/campaign_detail.html'


campaign_detail = CampaignDetailView.as_view()


@utils.auth_client_required
def campaign_create(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    form = forms.CampaignForm(
        client=client,
        initial={'min_friends_to_show': 1}
    )
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
