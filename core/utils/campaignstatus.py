import abc
import logging

from django.http import HttpResponseForbidden
from django.shortcuts import render

from core.utils import classregistry

from targetshare.models.relational import CampaignProperties


LOG = logging.getLogger('crow')


class StatusHandler(object):
    """Abstract base class for classes which define views' handling of campaign statuses."""

    __metaclass__ = classregistry.AutoRegistering
    _registry_ = {}

    @classmethod
    def __register__(cls):
        try:
            status = cls.status
        except AttributeError:
            pass
        else:
            cls._registry_[status] = cls

    @classmethod
    def select(cls, status):
        """Return the StatusHandler descendent which has registered itself for the given Status."""
        return cls._registry_[status]

    @classmethod
    @abc.abstractmethod
    def handle_request(cls, request, campaign):
        """Determine the validity of the given request for the given campaign.

        Concerete StatusHandlers handling statuses which are always allowed need not define this
        method, (though these classes will not be instantiable).

        If the request should not be allowed, the handler should raise an exception.
        (See DisallowedError.)

        """
        pass


class DisallowedError(StatusHandler, Exception):
    """Abstract extention to StatusHandler for statuses which define errors.

    Concrete descendents of DisallowedError may `raise` instances of themselves, to communicate
    the error to invoking scope, and provide to that scope their implementation of
    `make_error_response`.

    """
    def __init__(self, message, request, campaign):
        super(DisallowedError, self).__init__(message)
        self.request = request
        self.campaign = campaign

    @abc.abstractmethod
    def make_error_response(self, friendly=False):
        raise NotImplementedError


# Status handlers #

class Published(StatusHandler):

    status = CampaignProperties.Status.PUBLISHED

    # published status defines no special handling


class UnauthorizedPreview(DisallowedError):

    status = CampaignProperties.Status.DRAFT

    @classmethod
    def handle_request(cls, request, campaign):
        if (
            request.user.is_superuser or
            request.user.groups.filter(client=campaign.client).exists()
        ):
            # User is an authenticated member of the campaign client's auth group;
            # just note that we'll be giving them a preview:
            request.visit.events.first_or_create(
                event_type='client_preview',
                campaign=campaign,
                content=request.user.username,
            )
            return

        # User is unauthenticated or unauthorized
        LOG.warning("Received unauthorized request for draft campaign (%s)",
                    campaign.campaign_id, extra={'request': request})
        request.visit.events.create(
            event_type='preview_denied',
            campaign=campaign,
            content=request.user.username,
        )
        raise cls("Draft preview denied for unauthorized user", request, campaign)

    def make_error_response(self, friendly=False):
        if self.request.method == 'HEAD':
            return HttpResponseForbidden()

        return render(self.request, 'core/draft-forbidden.html', {
            'friendly': friendly,
            'client': self.campaign.client,
            'campaign': self.campaign,
        }, status=403)


def handle_request(request, campaign, properties=None):
    if properties is None:
        properties = campaign.campaignproperties.only('status').get()

    status = properties.status
    handler = StatusHandler.select(status)
    handler.handle_request(request, campaign)
    return status
