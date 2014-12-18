import logging

from django.http import HttpResponseForbidden
from django.template import Context, Template


LOG = logging.getLogger('crow')

FORBIDDEN_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Page under construction</h1>

        {% if friendly %}
        <p>
            Perhaps you'd like to
            <a href="{% url 'targetadmin:campaign-summary' client.pk campaign.pk %}">log in</a>
            first?
        </p>
        <p>Otherwise, check back in a bit!</p>
        {% endif %}
    </body>
    </html>
"""


class DraftMode(object):

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
        self.request = request
        self.campaign = campaign
        self.is_draft = is_draft
        self.is_allowed = is_allowed

    def __nonzero__(self):
        return self.is_draft
    __bool__ = __nonzero__

    def make_response(self, friendly=False):
        if self.is_allowed:
            return None

        if self.request.method == 'HEAD':
            content = ''
        else:
            context = Context({
                'friendly': friendly,
                'client': self.campaign.client,
                'campaign': self.campaign,
            })
            content = Template(FORBIDDEN_TEMPLATE).render(context)

        return HttpResponseForbidden(content)
