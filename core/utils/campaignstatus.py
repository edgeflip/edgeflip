import logging

from django.http import HttpResponseForbidden
from django.shortcuts import render


LOG = logging.getLogger('crow')


class CampaignStatusHandler(object):

    @classmethod
    def handle_request(cls, request, campaign, properties=None):
        if properties is None:
            campaign_status = campaign.campaignproperties.only('status').get()
        else:
            campaign_status = properties

        if campaign_status.status == campaign_status.Status.DRAFT:
            # Campaign is as yet unpublished
            if (
                not request.user.is_superuser and
                not request.user.groups.filter(client=campaign.client).exists()
            ):
                # User is unauthenticated or unauthorized
                LOG.warning("Received unauthorized request for draft campaign (%s)",
                            campaign.campaign_id, extra={'request': request})
                request.visit.events.create(
                    event_type='preview_denied',
                    campaign=campaign,
                    content=request.user.username,
                )
                return cls(request, campaign, is_draft=True, is_allowed=False)

            # User is an authenticated member of the campaign client's auth group;
            # just note that we'll be giving them a preview:
            request.visit.events.first_or_create(
                event_type='client_preview',
                campaign=campaign,
                content=request.user.username,
            )
            return cls(request, campaign, is_draft=True, is_allowed=True)

        # Campaign is published
        return cls(request, campaign, is_draft=False, is_allowed=True)

    def __init__(self, request, campaign, is_draft, is_allowed):
        self._request = request
        self._campaign = campaign
        self.is_draft = is_draft
        self.is_allowed = is_allowed

    def make_response(self, friendly=False):
        if self.is_allowed:
            return None

        if self._request.method == 'HEAD':
            return HttpResponseForbidden()

        return render(self._request, 'core/draft-forbidden.html', {
            'friendly': friendly,
            'client': self._campaign.client,
            'campaign': self._campaign,
        }, status=403)
