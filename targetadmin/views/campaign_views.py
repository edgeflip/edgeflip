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

    def get_context_data(self, **kwargs):
        context = super(CampaignDetailView, self).get_context_data(**kwargs)
        context.update({
            'properties': self.object.campaignproperties.for_datetime(datetime=None).get(),
            'choice_set': self.object.campaignchoicesets.for_datetime(datetime=None).get(),
        })
        return context


campaign_detail = CampaignDetailView.as_view()


@utils.auth_client_required
def campaign_create(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    if request.GET.get('clone_pk'):
        clone = get_object_or_404(
            relational.Campaign,
            pk=request.GET.get('clone_pk'),
            client=client
        )
        clone_props = clone.campaignproperties.get()
        initial = {
            'faces_url': clone_props.client_faces_url,
            'thanks_url': clone_props.client_thanks_url,
            'error_url': clone_props.client_error_url,
            'fallback_campaign': clone_props.fallback_campaign,
            'fallback_content': clone_props.fallback_content,
            'cascading_fallback': clone_props.fallback_is_cascading,
            'min_friends_to_show': clone_props.min_friends,
            'global_filter': clone.global_filter().filter if clone.global_filter() else None,
            'button_style': clone.button_style().button_style if clone.button_style() else None,
            'choice_set': clone.choice_set().choice_set if clone.choice_set() else None,
            'allow_generic': clone.choice_set().allow_generic if clone.choice_set() else False,
            'generic_url_slug': clone.choice_set().generic_url_slug if clone.choice_set() else None,
            'generic_fb_object': clone.generic_fb_object().fb_object if clone.generic_fb_object() else None,
            'fb_object': clone.fb_object().fb_object,
        }
    else:
        initial = {'min_friends_to_show': 1}

    form = forms.CampaignForm(
        client=client,
        initial=initial,
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
