import csv
import json
import logging
import re

from django.conf import settings
from django.core.mail import send_mail
from django.core.serializers import serialize
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from targetshare.models import relational
from targetshare.views.utils import encodeDES, JsonHttpResponse

from targetadmin import forms, utils


LOG_RVN = logging.getLogger('crow')


CAMPAIGN_CREATION_NOTIFICATION_MESSAGE = """\
Client Name: {client.name}
User Name: {username}
Campaign Name: {campaign.name}

Campaign Summary URL: {summary_url}
Campaign Snippets URL: {snippets_url}
Campaign URL: {campaign_url}

Please verify this campaign and its fallbacks.

Your friend,
The Campaign Wizard
"""

CAMPAIGN_CREATION_THANK_YOU_MESSAGE = (
    "Your campaign has been saved. "
    "Edgeflip is validating the campaign and "
    "will notify you when it has been deployed and ready for you to use."
)


def render_campaign_creation_message(request, campaign, content):
    client = campaign.client
    hostname = client.hostname
    sharing_urls = utils.build_sharing_urls(hostname, campaign, content)
    initial_url = "{scheme}//{host}{path}".format(
        scheme=settings.INCOMING_REQUEST_SCHEME,
        host=hostname,
        path=sharing_urls['initial_url'],
    )

    return CAMPAIGN_CREATION_NOTIFICATION_MESSAGE.format(
        username=request.user.username,
        campaign=campaign,
        client=client,
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


@utils.auth_client_required
@require_POST
def campaign_wizard(request, client_pk, campaign_pk=None):
    client = get_object_or_404(relational.Client, pk=client_pk)
    editing = campaign_pk and get_object_or_404(client.campaigns.root(), pk=campaign_pk)

    if editing:
        campaign_properties = editing.campaignproperties.get()
        if campaign_properties.status != campaign_properties.Status.DRAFT:
            return HttpResponseBadRequest("Only campaigns in draft mode can be modified")

        fb_attr_inst = editing.fb_object().fbobjectattribute_set.get()
    else:
        fb_attr_inst = relational.FBObjectAttribute(og_action='support', og_type='cause')

    fb_obj_form = forms.FBObjectWizardForm(request.POST, instance=fb_attr_inst)
    campaign_form = forms.CampaignWizardForm(request.POST)

    if not fb_obj_form.is_valid() or not campaign_form.is_valid():
        return JsonHttpResponse([fb_obj_form.errors, campaign_form.errors], status=400)

    campaign_name = campaign_form.cleaned_data['name']

    # Process tiered filter inputs
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

    # Create root filter whether we have filter features or not
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

    # Global Filter (currently unused)
    empty_filters = client.filters.filter(filterfeatures=None)
    if empty_filters.exists():
        global_filter = empty_filters[0]
    else:
        global_filter = client.filters.create(
            name='{} empty global filter'.format(client.name)
        )

    # Empty fallback filter
    # Need to make sure they didn't want a filterless campaign,
    # which would make the empty fallback irrelevant.
    if campaign_form.cleaned_data['include_empty_fallback'] and root_filter.filterfeatures.exists():
        # Find an empty choiceset filter group
        empty_choices = client.choicesets.filter(choicesetfilters__filter__filterfeatures=None)
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

    # Button Style (currently unused) TODO: remove
    if client.buttonstyles.exists():
        button_style = client.buttonstyles.all()[0]
    else:
        button_style = client.buttonstyles.create()

    # Page Styles
    page_style_sets = []
    for page in relational.Page.objects.all():
        client_styles = page.pagestyles.filter(starred=True, client=client)
        if client_styles:
            page_style_sets.append(client_styles)
        else:
            default_styles = page.pagestyles.filter(starred=True, client=None)
            page_style_sets.append(default_styles)

    # FB Object
    if editing:
        # Unlike with ChoiceSets etc., we update the existing FBObjectAttribute
        fb_obj = editing.fb_object()
        fb_obj_form.save()
    else:
        # Create fb object for new campaign
        fb_obj = client.fbobjects.create(name='{} {}'.format(client.name, campaign_name))
        fb_attr = fb_obj_form.save()
        fb_attr.fb_object = fb_obj
        fb_attr.save()

    # Client Content
    content_old = editing and campaign_properties.client_content
    new_url = campaign_form.cleaned_data['content_url']
    if content_old and content_old.url == new_url:
        # Original is OK
        content = content_old
    else:
        (content, _created) = client.clientcontent.first_or_create(url=new_url)

    campaign_chain = tuple(editing.iterchain()) if editing else []
    campaigns = []
    last_camp = None

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
                client_content=content,
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

            camp.campaignproperties.update(
                client_content=content,
                client_thanks_url=campaign_form.cleaned_data['thanks_url'],
                client_error_url=campaign_form.cleaned_data['error_url'],
                fallback_campaign=last_camp,
                fallback_is_cascading=bool(last_camp),
            )

        campaigns.append(camp)
        last_camp = camp

    faces_url = campaign_form.cleaned_data['faces_url']
    if not faces_url:
        slug = encodeDES('{}/{}'.format(last_camp.pk, content.pk))
        faces_url = 'https://apps.facebook.com/{}/{}/'.format(client.fb_app_name, slug)

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
        subject="{} {} campaign".format(client.name, "edited a" if editing else "created a new"),
        message=render_campaign_creation_message(request, last_camp, content),
        from_email=settings.ADMIN_FROM_ADDRESS,
        recipient_list=settings.ADMIN_NOTIFICATION_LIST,
        fail_silently=True,
    )
    return redirect('targetadmin:campaign-wizard-finish', client.pk, last_camp.pk)


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

        if (
            filter0 and
            not filter0.choicesetfilters.exists() and
            not filter0.campaignfbobject_set.exists() and
            not filter0.campaignglobalfilters.exists()
        ):
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


def advance_campaign_status(client_pk, campaign_pk, status):
    campaign = get_object_or_404(relational.Campaign.rootcampaigns,
                                 client_id=client_pk,
                                 campaign_id=campaign_pk)

    previous_state = status.previous
    if campaign.status() != previous_state:
        return HttpResponseBadRequest("Only campaigns in {} mode can be published"
                                      .format(previous_state))

    campaign.rootcampaign_properties.update(status=status)

    return redirect('targetadmin:campaign-summary', client_pk, campaign_pk)


@utils.auth_client_required
@require_POST
def publish_campaign(request, client_pk, campaign_pk):
    return advance_campaign_status(
        client_pk,
        campaign_pk,
        relational.CampaignProperties.Status.PUBLISHED,
    )


@utils.superuser_required
@require_POST
def archive_campaign(request, client_pk, campaign_pk):
    return advance_campaign_status(
        client_pk,
        campaign_pk,
        relational.CampaignProperties.Status.INACTIVE,
    )


@utils.auth_client_required
@require_GET
def campaign_summary(request, client_pk, campaign_pk, wizard=False):
    client = get_object_or_404(relational.Client, pk=client_pk)
    root_campaign = get_object_or_404(client.campaigns.root(), pk=campaign_pk)
    campaign_properties = root_campaign.campaignproperties.get()
    content = campaign_properties.client_content

    filters = []
    for campaign in root_campaign.iterchain():
        filters.append([
            list(choice_set_filter.filter.filterfeatures.values(
                'feature', 'operator', 'value', 'feature_type__code',
            ).iterator())
            for choice_set_filter in campaign.choice_set().choicesetfilters.all()
        ])

    fb_obj_attributes = root_campaign.fb_object().fbobjectattribute_set.values(
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
    ).get()

    (serialized_properties,) = serialize('python', (campaign_properties,), fields=(
        'client_faces_url',
        'client_thanks_url',
        'client_error_url',
        'status',
    ))

    summary_data = {
        'campaign_id': root_campaign.pk,
        'create_dt': root_campaign.create_dt.isoformat(),
        'client': client,
        'content_url': content.url,
        'campaign_name': re.sub(r' 1$', '', root_campaign.name),
        'root_campaign': root_campaign,
        'campaign_properties': json.dumps(serialized_properties['fields']),
        'fb_obj_attributes': json.dumps(fb_obj_attributes),
        'filters': json.dumps(filters),
    }

    if campaign_properties.status < campaign_properties.Status.INACTIVE:
        incoming_host = client.hostname
        sharing_urls = utils.build_sharing_urls(incoming_host, root_campaign, content)
        summary_data['sharing_url'] = '{}//{}{}'.format(settings.INCOMING_REQUEST_SCHEME,
                                                        incoming_host,
                                                        sharing_urls['initial_url'])

    if wizard:
        summary_data['message'] = CAMPAIGN_CREATION_THANK_YOU_MESSAGE

    return render(request, 'targetadmin/campaign_summary_page.html', summary_data)


@utils.auth_client_required
@require_GET
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
@require_GET
def campaign_data(request, client_pk, campaign_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    campaign = get_object_or_404(client.campaigns.root(), pk=campaign_pk)
    campaign_properties = campaign.campaignproperties.get()
    content = campaign_properties.client_content

    campaign_filters = []
    for campaign0 in campaign.iterchain():
        try:
            choice_set_filter = campaign0.choice_set().choicesetfilters.get()
        except relational.ChoiceSetFilter.DoesNotExist:
            fallback_features = ()
        else:
            fallback_features = list(
                choice_set_filter.filter.filterfeatures.values(
                    'feature', 'value', 'operator', 'feature_type__code',
                ).iterator()
            )
            if fallback_features:
                campaign_filters.append(fallback_features)

    empty_fallback = bool(campaign_properties.fallback_campaign) and not fallback_features

    # We want to hide the facebook url in draft mode if the client isn't hosting
    faces_url = campaign_properties.client_faces_url
    if faces_url.startswith('https://apps.facebook.com/'):
        faces_url = ''

    fb_attr_inst = campaign.fb_object().fbobjectattribute_set.get()

    return JsonHttpResponse({
        'name': re.sub(r' 1$', '', campaign.name),
        'faces_url': faces_url,
        'error_url': campaign_properties.client_error_url,
        'thanks_url': campaign_properties.client_thanks_url,
        'content_url': content.url,
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
        'sharing_button': fb_attr_inst.sharing_button,
    })
