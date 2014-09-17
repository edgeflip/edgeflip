import csv
import json
import logging
import re

from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from targetshare.models import relational
from targetshare.utils import encodeDES
from targetshare.views.utils import JsonHttpResponse

from targetadmin import forms, utils
from targetadmin.views import base


LOG_RVN = logging.getLogger('crow')


CAMPAIGN_CREATION_NOTIFICATION_MESSAGE = """\
Client Name: {client.name}
Campaign Name: {campaign.name}

Campaign Summary URL: {summary_url}
Campaign Snippets URL: {snippets_url}
Campaign URL: {campaign_url}

Please verify this campaign and its fallbacks.

Your friend,
The Campaign Wizard
"""

CAMPAIGN_CREATION_THANK_YOU_MESSAGE = """\
Your campaign has been saved. Edgeflip is validating the campaign \
and will notify you when it has been deployed and ready for you to use.\
"""


def render_campaign_creation_message(request, campaign, content):
    hostname = request.get_host()
    sharing_urls = utils.build_sharing_urls(hostname, campaign, content)
    initial_url = "{scheme}//{host}{path}".format(
        scheme=('https:' if utils.INCOMING_SECURE else 'http:'),
        host=hostname,
        path=sharing_urls['initial_url'],
    )

    return CAMPAIGN_CREATION_NOTIFICATION_MESSAGE.format(
        campaign=campaign,
        client=campaign.client,
        summary_url=request.build_absolute_uri(
            reverse('targetadmin:campaign-summary', args=[campaign.client.pk, campaign.pk])
        ),
        snippets_url=request.build_absolute_uri(
            "{}?campaign_pk={}&content_pk={}".format(
                reverse('targetadmin:snippets', args=[campaign.client.pk]),
                campaign.pk,
                content.pk,
            )
        ),
        campaign_url=initial_url,
    )


class CampaignListView(base.ClientRelationListView):
    model = relational.Campaign
    object_string = 'Campaign'
    detail_url_name = 'targetadmin:campaign-detail'
    create_url_name = 'targetadmin:campaign-new'


campaign_list = CampaignListView.as_view()


class CampaignDetailView(base.ClientRelationDetailView):
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
    clone_pk = request.GET.get('clone_pk')
    if clone_pk:
        clone = get_object_or_404(relational.Campaign, pk=clone_pk, client=client)
        clone_props = clone.campaignproperties.get()
        campaign_choice_set = clone.campaign_choice_set()
        initial = {
            'faces_url': clone_props.client_faces_url,
            'thanks_url': clone_props.client_thanks_url,
            'error_url': clone_props.client_error_url,
            'fallback_campaign': clone_props.fallback_campaign,
            'fallback_content': clone_props.fallback_content,
            'cascading_fallback': clone_props.fallback_is_cascading,
            'min_friends_to_show': clone_props.min_friends,
            'global_filter': clone.global_filter(),
            'button_style': clone.button_style(),
            'choice_set': campaign_choice_set and campaign_choice_set.choice_set,
            'allow_generic': campaign_choice_set.allow_generic if campaign_choice_set else False,
            'generic_url_slug': campaign_choice_set and campaign_choice_set.generic_url_slug,
            'generic_fb_object': clone.generic_fb_object(),
            'fb_object': clone.fb_object(),
        }
    else:
        initial = {'min_friends_to_show': 1}

    if request.method == 'POST':
        form = forms.CampaignForm(client=client, data=request.POST)
        if form.is_valid():
            campaign = form.save()
            return redirect('targetadmin:campaign-detail', client.pk, campaign.pk)
    else:
        form = forms.CampaignForm(client=client, initial=initial)

    return render(request, 'targetadmin/campaign_edit.html', {
        'client': client,
        'form': form
    })


@utils.auth_client_required
def campaign_wizard(request, client_pk, campaign_pk=None):
    client = get_object_or_404(relational.Client, pk=client_pk)
    campaign = campaign_pk and get_object_or_404(client.campaigns, pk=campaign_pk)
    if request.method == 'POST':
        old_content = None
        if campaign:
            fb_attr_inst = campaign.fb_object().fbobjectattribute_set.get()
            campaign_properties = campaign.campaignproperties.get()
            old_content = guess_content(client, campaign)

            if campaign_properties.status != relational.CampaignProperties.Status.DRAFT:
                return HttpResponseBadRequest("Only campaigns in draft mode can be modified")
        else:
            fb_attr_inst = relational.FBObjectAttribute(og_action='support', og_type='cause')
        fb_obj_form = forms.FBObjectWizardForm(request.POST, instance=fb_attr_inst)
        campaign_form = forms.CampaignWizardForm(request.POST)

        if fb_obj_form.is_valid() and campaign_form.is_valid():
            campaign_name = campaign_form.cleaned_data['name']

            filter_feature_layers = []
            ranking_feature_layers = []
            enabled_filters = (request.POST.get('enabled-filters-{}'.format(index), '')
                               for index in xrange(1, 5))
            for inputs in csv.reader(enabled_filters):
                if not inputs:
                    continue

                filter_feature_layer = []
                ranking_feature_layer = []
                for feature_string in inputs:
                    (feature, operator, value) = feature_string.split('.', 2)
                    if feature == 'interest':
                        feature = 'topics[{}]'.format(value)
                        operator = relational.FilterFeature.Operator.MIN
                        value = settings.ADMIN_TOPICS_FILTER_THRESHOLD

                        # topics filters also get a ranking:
                        try:
                            ranking_key_feature = relational.RankingKeyFeature.objects.filter(
                                feature=feature,
                                reverse=True,
                                ranking_key__client=client,
                            )[0]
                        except IndexError:
                            ranking_key_feature = relational.RankingKeyFeature(
                                feature=feature,
                                feature_type=relational.RankingFeatureType.objects.get_topics(),
                                reverse=True,
                            )
                        else:
                            ranking_key_feature.pk = None

                        ranking_feature_layer.append(ranking_key_feature)

                    try:
                        # Go for an existing one
                        ff = relational.FilterFeature.objects.filter(
                            feature=feature,
                            operator=operator,
                            value=value,
                            filter__client=client,
                        )[0]
                    except IndexError:
                        # It'll get saved further down below
                        ff = relational.FilterFeature(
                            feature=feature,
                            operator=operator,
                            value=value,
                        )
                    else:
                        ff.pk = None

                    filter_feature_layer.append(ff)

                filter_feature_layers.append(filter_feature_layer)
                ranking_feature_layers.append(ranking_feature_layer)

            # Create root filter whether we have filter features or not:
            root_filter = client.filters.create(
                name='{} {} Root Filter'.format(client.name, campaign_name),
            )
            root_choiceset = client.choicesets.create(
                name='{} {} Root ChoiceSet'.format(client.name, campaign_name),
            )
            root_choiceset.choicesetfilters.create(filter=root_filter)
            choice_sets = [root_choiceset]

            # Assign filter features:
            for (layer_count, filter_feature_layer) in enumerate(filter_feature_layers):
                try:
                    cs = choice_sets[layer_count]
                except IndexError:
                    choice_set_filter = client.filters.create(
                        name='{} {}'.format(client.name, campaign_name),
                    )
                    cs = client.choicesets.create(name=campaign_name)
                    cs.choicesetfilters.create(filter=choice_set_filter)
                    choice_sets.append(cs)
                else:
                    choice_set_filter = cs.choicesetfilters.get().filter

                for feature in filter_feature_layer:
                    feature.pk = None
                    feature.filter = choice_set_filter
                    feature.save()

            if ranking_feature_layers:
                ranking_keys = []
                for ranking_feature_layer in ranking_feature_layers:
                    if ranking_feature_layer:
                        ranking_key = client.rankingkeys.create(
                            name='{} {}'.format(client.name, campaign_name),
                        )
                        for (feature_index, ranking_key_feature) in enumerate(ranking_feature_layer):
                            ranking_key_feature.pk = None
                            ranking_key_feature.ranking_key = ranking_key
                            ranking_key_feature.ordinal_position = feature_index
                            ranking_key_feature.save()
                    else:
                        ranking_key = None

                    ranking_keys.append(ranking_key)
            else:
                # Campaign defines no filtering at all;
                # but we'll still have a root filter in `choice_sets` to match:
                ranking_keys = [None]

            # TODO: get or create ClientContent based on URL
            content = client.clientcontent.create(
                name='{} {}'.format(client.name, campaign_name),
                url=campaign_form.cleaned_data.get('content_url'),
            )

            if old_content:
                old_content.delete()

            # Global Filter
            empty_filters = client.filters.filter(filterfeatures=None)
            if empty_filters.exists():
                global_filter = empty_filters[0]
            else:
                global_filter = client.filters.create(
                    name='{} empty global filter'.format(client.name)
                )

            # Button Style
            if client.buttonstyles.exists():
                button_style = client.buttonstyles.all()[0]
            else:
                button_style = client.buttonstyles.create()

            # Need to make sure they didn't want a filterless campaign,
            # which would make the empty fallback irrelevant.
            if (campaign_form.cleaned_data['include_empty_fallback'] and
               root_filter.filterfeatures.exists()):
                # Find an empty choiceset filter group
                empty_choices = client.choicesets.filter(
                    choicesetfilters__filter__filterfeatures=None,
                )
                if empty_choices.exists():
                    empty_cs = empty_choices[0]
                else:
                    empty_cs = client.choicesets.create(
                        name='{} {} Empty ChoiceSet'.format(client.name, campaign_name)
                    )
                    # Already have a known empty filter
                    empty_cs.choicesetfilters.create(filter=global_filter)
                choice_sets.append(empty_cs)
                ranking_keys.append(None)

            # Page Styles
            page_style_sets = []
            for page in relational.Page.objects.all():
                client_styles = page.pagestyles.filter(
                    starred=True,
                    client=client,
                )
                if client_styles:
                    page_style_sets.append(client_styles)
                else:
                    default_styles = page.pagestyles.filter(
                        starred=True,
                        client=None,
                    )
                    page_style_sets.append(default_styles)

            campaign_chain = []
            if campaign:
                campaign_chain.append(campaign)
                fallback_campaign = campaign_properties.fallback_campaign
                while fallback_campaign:
                    campaign_chain.append(fallback_campaign)
                    fallback_campaign = fallback_campaign.campaignproperties.get().fallback_campaign

                # NOTE: Unlike with ChoiceSets etc., we update the existing FBObjectAttribute
                fb_obj = campaign.fb_object()
                fb_obj_form.save()
            else:
                # Only create fb object for new campaign
                fb_obj = client.fbobjects.create(
                    name='{} {}'.format(client.name, campaign_name),
                )
                fb_attr = fb_obj_form.save()
                fb_attr.fb_object = fb_obj
                fb_attr.save()

            last_camp = None
            campaigns = []

            for (rank, cs, ranking_key) in reversed(zip(range(len(choice_sets)),
                                                        choice_sets,
                                                        ranking_keys)):
                try:
                    camp = campaign_chain[rank]
                except IndexError:
                    camp = client.campaigns.create(name='{} {}'.format(campaign_name, rank + 1))
                    camp.campaignbuttonstyles.create(button_style=button_style, rand_cdf=1.0)
                    camp.campaignglobalfilters.create(filter=global_filter, rand_cdf=1.0)
                    camp.campaignfbobjects.create(fb_object=fb_obj, rand_cdf=1.0)
                    camp.campaignchoicesets.create(choice_set=cs, rand_cdf=1.0)
                    if ranking_key:
                        camp.campaignrankingkeys.create(ranking_key=ranking_key)

                    camp.campaignproperties.create(
                        client_faces_url=campaign_form.cleaned_data['faces_url'],
                        client_thanks_url=campaign_form.cleaned_data['thanks_url'],
                        client_error_url=campaign_form.cleaned_data['error_url'],
                        fallback_campaign=last_camp,
                        fallback_is_cascading=bool(last_camp),
                    )

                    for page_styles in page_style_sets:
                        page_style_set = relational.PageStyleSet.objects.create()
                        page_style_set.page_styles = page_styles
                        camp.campaignpagestylesets.create(
                            page_style_set=page_style_set,
                            rand_cdf=1.0,
                        )
                else:
                    camp.name = '{} {}'.format(campaign_name, rank + 1)
                    camp.save()
                    camp.campaignbuttonstyles.update(button_style=button_style, rand_cdf=1.0)

                    clean_up_campaign(camp)
                    camp.campaignchoicesets.update(choice_set=cs) # update campaign to new ChoiceSet
                    if ranking_key:
                        camp.campaignrankingkeys.create(ranking_key=ranking_key)

                    faces_url = (campaign_form.cleaned_data['faces_url'] or
                                 camp.campaignproperties.get().client_faces_url)

                    camp.campaignproperties.update(
                        client_faces_url=faces_url,
                        client_thanks_url=campaign_form.cleaned_data['thanks_url'],
                        client_error_url=campaign_form.cleaned_data['error_url'],
                        fallback_campaign=last_camp,
                        fallback_is_cascading=bool(last_camp),
                    )

                campaigns.append(camp)
                last_camp = camp

            # Check to see if we need to generate the faces_url
            stored_faces_url = last_camp.campaignproperties.get().client_faces_url
            if campaign_form.cleaned_data['faces_url']:
                faces_url = campaign_form.cleaned_data['faces_url']
            elif stored_faces_url:
                faces_url = stored_faces_url
            else:
                encoded_url = encodeDES('{}/{}'.format(last_camp.pk, content.pk))
                faces_url = 'https://apps.facebook.com/{}/{}/'.format(client.fb_app_name, encoded_url)

            for campaign in campaigns:
                properties = campaign.campaignproperties.get()
                properties.client_faces_url = faces_url
                properties.root_campaign = last_camp
                properties.save()

            discarded_fallbacks = campaign_chain[len(campaigns):]
            for index in reversed(range(len(discarded_fallbacks))):
                if index > 0:
                    # Break chain link:
                    discarded_fallback1 = discarded_fallbacks[index - 1]
                    discarded_fallback1.campaignproperties.update(fallback_campaign=None)

                discarded_fallback = discarded_fallbacks[index]

                # Check for extraordinary links from other chains:
                if discarded_fallback.fallbackcampaign_properties.exists():
                    LOG_RVN.error("Campaign in use by multiple fallback chains, clean-up deferred at %s %r",
                                  discarded_fallback.pk,
                                  [discarded.pk for discarded in discarded_fallbacks],
                                  extra={'request': request})
                    break

                clean_up_campaign(discarded_fallback)
                discarded_fallback.delete()

            send_mail(
                subject="{} created a new campaign".format(client.name),
                message=render_campaign_creation_message(request, last_camp, content),
                from_email=settings.ADMIN_FROM_ADDRESS,
                recipient_list=settings.ADMIN_NOTIFICATION_LIST,
                fail_silently=True,
            )
            response = redirect('targetadmin:campaign-wizard-finish',
                                client.pk, last_camp.pk)
            # FIXME
            response['Location'] += "?content={}".format(content.pk)
            return response


@utils.auth_client_required
def campaign_summary(request, client_pk, campaign_pk):
    return render(
        request,
        'targetadmin/campaign_summary_page.html',
        get_campaign_summary_data(request, client_pk, campaign_pk)
    )


@utils.auth_client_required
def campaign_wizard_finish(request, client_pk, campaign_pk):
    content_pk = request.GET.get('content', '')
    if content_pk.isdigit():
        summary_data = get_campaign_summary_data(request, client_pk, campaign_pk, content_pk)
        summary_data['message'] = CAMPAIGN_CREATION_THANK_YOU_MESSAGE
        return render(
            request,
            'targetadmin/campaign_summary_page.html',
            summary_data
        )

    return HttpResponseBadRequest("Client content is required.") # FIXME


def guess_content(client, root_campaign):
    # FIXME
    return relational.ClientContent.objects.filter(
        name='{} {}'.format(client.name, root_campaign.name[:-2])
    )[0]


def get_campaign_summary_data(request, client_pk, campaign_pk, content_pk=None):
    client = get_object_or_404(relational.Client, pk=client_pk)
    root_campaign = get_object_or_404(client.campaigns, pk=campaign_pk)

    if content_pk:
        content = get_object_or_404(client.clientcontent, pk=content_pk)
    else:
        content = guess_content(client, root_campaign)

    filters = []
    campaign1 = root_campaign
    while campaign1:
        filters.append([
            list(choice_set_filter.filter.filterfeatures.values(
                'feature', 'operator', 'value', 'feature_type__code',
            ).iterator())
            for choice_set_filter in campaign1.choice_set().choicesetfilters.all()
        ])
        properties1 = campaign1.campaignproperties.get()
        campaign1 = properties1.fallback_campaign

    fb_obj_attributes = root_campaign.fb_object().fbobjectattribute_set
    root_properties = root_campaign.campaignproperties.values(
        'client_faces_url',
        'client_thanks_url',
        'client_error_url',
        'status',
    ).get()

    base_values = {
        'campaign_id': campaign_pk,
        'client': client,
        'content_url': content.url,
        'campaign_name': re.sub(r' 1$', '', root_campaign.name),
        'root_campaign': root_campaign,
        'campaign_properties': json.dumps(root_properties),
        'fb_obj_attributes': json.dumps(fb_obj_attributes.values(
            'msg1_post',
            'msg1_pre',
            'msg2_post',
            'msg2_pre',
            'og_description',
            'og_image',
            'og_title',
            'og_type',
            'org_name',
            'sharing_prompt',
            'sharing_sub_header',
        ).get()),
        'filters': json.dumps(filters),
    }

    if (
        request.user.is_superuser or
        root_properties['status'] == relational.CampaignProperties.Status.PUBLISHED
    ):
        sharing_urls = utils.build_sharing_urls(request.get_host(), root_campaign, content)
        base_values['sharing_url'] = 'https://{}.{}{}'.format(client.subdomain,
                                                              client.domain,
                                                              sharing_urls['initial_url'])

    return base_values


def clean_up_campaign(campaign):
    # clean up choice set
    choice_set = campaign.choice_set()
    if choice_set.campaignchoicesets.count() == 1:
        # Old ChoiceSet is not in use by any other Campaign, so let's clean it up:
        try:
            csf0 = choice_set.choicesetfilters.get()
        except relational.ChoiceSetFilter.DoesNotExist:
            filter0 = None
        else:
            filter0 = csf0.filter

        if filter0 and filter0.filterfeatures.exists(): # long live the empty choice set
            campaign.campaignchoicesets.update(choice_set=None) # prevent cascading delete of CampaignChoiceSet
            choice_set.delete()

        if filter0 and not filter0.choicesetfilters.exists() and not filter0.campaignfbobject_set.exists() and not filter0.campaignglobalfilters.exists():
            # Old ChoiceSet's Filter isn't in use anymore, so let's clean that up:
            filter0.delete()

    # clean up ranking_keys:
    try:
        campaign_ranking_key0 = campaign.campaignrankingkeys.get()
    except relational.CampaignRankingKey.DoesNotExist:
        pass
    else:
        ranking_key0 = campaign_ranking_key0.ranking_key
        campaign_ranking_key0.delete()
        if not ranking_key0.campaignrankingkeys.exists():
            ranking_key0.delete()


@utils.auth_client_required
def available_filters(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    filter_features = relational.FilterFeature.objects.filter(
        filter__client=client,
        feature__isnull=False,
        operator__isnull=False,
        value__isnull=False,
    ).values('feature', 'operator', 'value', 'feature_type__code').distinct()
    return JsonHttpResponse(list(filter_features.iterator()))


@utils.auth_client_required
def campaign_data(request, client_pk, campaign_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    campaign = get_object_or_404(client.campaigns, pk=campaign_pk)
    campaign_properties = campaign.campaignproperties.get()

    fb_attr_inst = campaign.fb_object().fbobjectattribute_set.get()

    campaign_filters = [list(
        campaign.choice_set().choicesetfilters.get().filter.filterfeatures.values(
            'feature', 'value', 'operator', 'feature_type__code'
        )
    )]

    fallback_campaign = campaign_properties.fallback_campaign
    while fallback_campaign:
        last_campaign = fallback_campaign
        try:
            choice_set_filter = fallback_campaign.choice_set().choicesetfilters.get()
        except relational.ChoiceSetFilter.DoesNotExist:
            fallback_features = ()
        else:
            fallback_features = choice_set_filter.filter.filterfeatures.values(
                'feature', 'value', 'operator', 'feature_type__code')
        if fallback_features:
            campaign_filters.append(list(fallback_features))
        fallback_campaign = fallback_campaign.campaignproperties.get().fallback_campaign

    empty_fallback = (bool(campaign_properties.fallback_campaign) and
                      not last_campaign.choice_set().choicesetfilters.exists())

    # We want to hide the facebook url in draft mode if the client isn't hosting
    faces_url = campaign_properties.client_faces_url
    if 'https://apps.facebook.com' in faces_url:
        faces_url = ''

    return JsonHttpResponse({
        'name': re.sub(r' 1$', '', campaign.name),
        'faces_url': faces_url,
        'error_url': campaign_properties.client_error_url,
        'thanks_url': campaign_properties.client_thanks_url,
        'content_url': campaign_properties.client_thanks_url,
        'include_empty_fallback': empty_fallback,
        'filters': campaign_filters,
        'msg1_post': fb_attr_inst.msg1_post,
        'msg1_pre': fb_attr_inst.msg1_pre,
        'msg2_post': fb_attr_inst.msg2_post,
        'msg2_pre': fb_attr_inst.msg2_pre,
        'org_name': fb_attr_inst.org_name,
        'og_title': fb_attr_inst.og_title,
        'og_image': fb_attr_inst.og_image,
        'og_description': fb_attr_inst.og_description,
        'sharing_prompt': fb_attr_inst.sharing_prompt,
        'sharing_sub_header': fb_attr_inst.sharing_sub_header,
        'sharing_button': fb_attr_inst.sharing_button
    })
