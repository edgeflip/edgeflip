from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from targetadmin import utils
from targetadmin import forms
from targetshare.models import relational
from targetshare.utils import encodeDES
from targetadmin.views.base import (
    ClientRelationListView,
    ClientRelationDetailView,
)


class CampaignListView(ClientRelationListView):
    model = relational.Campaign
    object_string = 'Campaign'
    detail_url_name = 'targetadmin:campaign-detail'
    create_url_name = 'targetadmin:campaign-new'


campaign_list = CampaignListView.as_view()


class CampaignDetailView(ClientRelationDetailView):
    model = relational.Campaign
    object_string = 'Campaign'
    edit_url_name = 'targetadmin:campaign-edit'
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
            return redirect('targetadmin:campaign-detail', client.pk, campaign.pk)

    return render(request, 'targetadmin/campaign_edit.html', {
        'client': client,
        'form': form
    })


@utils.auth_client_required
def campaign_wizard(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    fb_obj_form = forms.FBObjectWizardForm()
    campaign_form = forms.CampaignWizardForm()
    if request.method == 'POST':
        fb_obj_form = forms.FBObjectWizardForm(request.POST)
        campaign_form = forms.CampaignWizardForm(request.POST)
        if fb_obj_form.is_valid() and campaign_form.is_valid() and request.POST.get('enabled-filters-1'):
            campaign_name = campaign_form.cleaned_data['name']
            filter_feature_layers = []
            for x in xrange(1, 5):
                inputs = request.POST.get('enabled-filters-{}'.format(x))
                if not inputs:
                    continue

                inputs = inputs.split(',')
                layer = []
                for feature_string in inputs:
                    feature, operator, value = feature_string.split('.')
                    ff = relational.FilterFeature.objects.filter(
                        feature=feature, operator=operator, value=value,
                    )[0]
                    ff.pk = None
                    ff.save()
                    layer.append(ff)
                filter_feature_layers.append(layer)

            root_filter = relational.Filter.objects.create(
                name='{} {} Root Filter'.format(
                    client.name,
                    campaign_name,
                ),
                client=client
            )
            for feature in filter_feature_layers[0]:
                feature.filter = root_filter
                feature.save()

            root_choiceset = relational.ChoiceSet.objects.create(
                name='{} {} Root ChoiceSet'.format(
                    client.name,
                    campaign_name
                ),
                client=client
            )
            root_choiceset.choicesetfilters.create(
                filter=root_filter)
            del filter_feature_layers[0]

            choice_sets = {0: root_choiceset}
            # First layer is the root_choiceset
            layer_count = 1
            while filter_feature_layers:
                for layer in filter_feature_layers:
                    for feature in layer:
                        cs = choice_sets.get(layer_count)
                        if not cs:
                            single_filter = relational.Filter.objects.create(
                                name='{} {} {}'.format(
                                    client.name, campaign_name, feature.feature),
                                client=client
                            )
                            cs = relational.ChoiceSet.objects.create(
                                client=client,
                                name=campaign_name
                            )
                            relational.ChoiceSetFilter.objects.create(
                                filter=single_filter,
                                choice_set=cs
                            )
                            choice_sets[layer_count] = cs
                        feature.pk = None
                        feature.filter = cs.choicesetfilters.get().filter
                        feature.save()
                    layer_count += 1
                    filter_feature_layers.remove(layer)

            fb_obj = relational.FBObject.objects.create(
                name='{} {} {}'.format(client.name, campaign_name, timezone.now()),
                client=client
            )
            fb_attr = fb_obj_form.save()
            fb_attr.fb_object = fb_obj
            fb_attr.save()

            content = relational.ClientContent.objects.create(
                url=campaign_form.cleaned_data.get('content_url'),
                client=client,
                name='{} {}'.format(client.name, campaign_name)
            )

            # Global Filter
            empty_filters = client.filters.filter(filterfeatures__isnull=True)
            if empty_filters.exists():
                global_filter = empty_filters[0]
            else:
                global_filter = client.filters.create(
                    name='{} empty global filter'.format(client.name))

            # Button Style
            if client.buttonstyles.exists():
                button_style = client.buttonstyles.all()[0]
            else:
                button_style = client.buttonstyles.create()

            # final fallback campaign init
            # Find an empty choiceset filter group
            empty_choices = client.choicesets.filter(
                choicesetfilters__filter__filterfeatures__isnull=True)
            if empty_choices.exists():
                empty_cs = empty_choices[0]
            else:
                empty_cs = client.choicesets.create(
                    name='{} {} Empty ChoiceSet'.format(
                        client.name, campaign_name)
                )
                # Already have a known empty filter
                empty_cs.choicesetfilters.create(filter=global_filter)
            # Find the end of the choice_sets dict
            rank = max(choice_sets) + 1
            choice_sets[rank] = empty_cs

            last_camp = None
            campaigns = []
            for rank, cs in sorted(choice_sets.iteritems(), reverse=True):
                camp = relational.Campaign.objects.create(
                    client=client,
                    name='{} {}'.format(campaign_name, rank + 1),
                )
                camp.campaignbuttonstyles.create(button_style=button_style, rand_cdf=1.0)
                camp.campaignglobalfilters.create(filter=global_filter, rand_cdf=1.0)
                camp.campaignchoicesets.create(choice_set=cs, rand_cdf=1.0)
                camp.campaignproperties.create(
                    client_faces_url=campaign_form.cleaned_data['faces_url'],
                    client_thanks_url=campaign_form.cleaned_data['thanks_url'],
                    client_error_url=campaign_form.cleaned_data['error_url'],
                    fallback_campaign=last_camp,
                    fallback_is_cascading=True,
                )
                camp.campaignfbobjects.create(
                    fb_object=fb_obj,
                    rand_cdf=1.0
                )
                campaigns.append(camp)
                last_camp = camp

            # Check to see if we need to generate the faces_url
            if campaign_form.cleaned_data['faces_url']:
                faces_url = campaign_form.cleaned_data['faces_url']
            else:
                encoded_url = encodeDES('{}/{}'.format(
                    last_camp.pk, content.pk))
                faces_url = 'https://apps.facebook.com/{}/{}/'.format(
                    client.fb_app_name, encoded_url)

            for camp in campaigns:
                properties = camp.campaignproperties.get()
                properties.client_faces_url = faces_url
                properties.root_campaign = last_camp
                properties.save()

            send_mail(
                '{} Created New Campaigns'.format(client.name),
                'Campaign PK: {} created. Please verify it and its children.'.format(last_camp.pk),
                settings.ADMIN_FROM_ADDRESS,
                settings.ADMIN_NOTIFICATION_LIST,
                fail_silently=True
            )
            return redirect(
                'targetadmin:campaign-wizard-finish',
                client.pk, last_camp.pk, content.pk
            )
    return render(request, 'targetadmin/campaign_wizard.html', {
        'client': client,
        'fb_obj_form': fb_obj_form,
        'campaign_form': campaign_form,
        'filter_features': relational.FilterFeature.objects.filter(
            filter__client=client, feature__isnull=False,
            operator__isnull=False, value__isnull=False)
        .values('feature', 'operator', 'value').distinct()
    })


@utils.auth_client_required
def campaign_wizard_finish(request, client_pk, campaign_pk, content_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    root_campaign = get_object_or_404(relational.Campaign, pk=campaign_pk)
    properties = root_campaign.campaignproperties.get()
    content = get_object_or_404(relational.ClientContent, pk=content_pk)
    campaigns = []
    has_fallbacks = True
    while has_fallbacks:
        campaigns.append(properties)
        has_fallbacks = True if properties.fallback_campaign else False
        if has_fallbacks:
            properties = properties.fallback_campaign.campaignproperties.get()
    return render(request, 'targetadmin/campaign_wizard_finish.html', {
        'campaigns': campaigns,
        'content': content,
        'client': client,
    })
