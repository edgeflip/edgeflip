import json

from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.shortcuts import redirect
from django.core.serializers.json import DjangoJSONEncoder

from targetadmin import forms, utils
from targetshare.models import relational
from targetadmin.views.base import CRUDView


class ClientListView(ListView):
    model = relational.Client,
    template_name = 'targetadmin/home.html'
    queryset = relational.Client.objects.all()

    def get(self, request):
        # Check for only one client
        try:
            client_id = self.get_queryset().values_list('pk', flat=True).get()
        except (relational.Client.DoesNotExist, relational.Client.MultipleObjectsReturned):
            pass
        else:
            return redirect('targetadmin:client-detail', client_id)

        return super(ClientListView, self).get(request)

    def get_queryset(self):
        queryset = super(ClientListView, self).get_queryset()
        if self.request.user.is_superuser:
            return queryset
        else:
            return queryset.filter(
                auth_groups__user=self.request.user
            ).distinct()


class ClientDetailView(DetailView):
    model = relational.Client
    pk_url_kwarg = 'client_pk'

    def get_template_names(self):
        return ['targetadmin/{}'.format(
            'superuser_home.html' if self.request.user.is_superuser else 'client_home.html')]

    def get_context_data(self, **kwargs):
        context = super(ClientDetailView, self).get_context_data(**kwargs)
        root_campaigns = context['client'].campaigns\
            .exclude(rootcampaign_properties=None)\
            .order_by( '-create_dt' )
        campaigns = [ item for item in root_campaigns.values('pk', 'create_dt', 'name') ]
        for i, campaign in enumerate(root_campaigns):
            campaigns[i]['filters'] = []
            campaign1 = campaign
            while campaign1:
                try:
                    if campaign1.choice_set() is not None:
                        for choice_set_filter in campaign1.choice_set().choicesetfilters.all():
                            campaigns[i]['filters'].append([
                                list(choice_set_filter.filter.filterfeatures.values(
                                    'feature', 'operator', 'value', 'feature_type__code',
                                ).iterator())
                            ])
                except relational.CampaignChoiceSet.MultipleObjectsReturned:
                    pass

                try:
                    properties1 = campaign1.campaignproperties.get()
                except relational.CampaignProperties.MultipleObjectsReturned:
                    pass
                campaign1 = properties1.fallback_campaign

            campaigns[i]['properties'] = list(campaign.campaignproperties.values())[0]

            try:
                campaigns[i]['fb_obj_attributes'] = list(campaign.fb_object().fbobjectattribute_set.values())[0]
            except relational.CampaignFBObject.MultipleObjectsReturned:
                pass

        context['campaigns'] = campaigns

        return context

    def render_to_response(self, context, **response_kwargs):
        return self.response_class(
            request=self.request,
            template=self.get_template_names(),
            context=dict(
                campaigns=json.dumps(list(context['campaigns']), cls=DjangoJSONEncoder),
                client=context['client']),
            **response_kwargs
        ) 

class ClientFormView(CRUDView):
    template_name = 'targetadmin/client_edit.html'
    form_class = forms.ClientForm
    success_url = 'targetadmin:client-detail'
    queryset = relational.Client.objects.all()

client_list_view = login_required(ClientListView.as_view(), login_url='targetadmin:login')
client_detail_view = utils.auth_client_required(ClientDetailView.as_view())
client_form_view = ClientFormView.as_view()
