import csv
import itertools

from django.conf import settings
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
    fb_attr_inst = relational.FBObjectAttribute(
        og_action='support', og_type='cause')
    fb_obj_form = forms.FBObjectWizardForm(instance=fb_attr_inst)
    campaign_form = forms.CampaignWizardForm()
    if request.method == 'POST':
        fb_obj_form = forms.FBObjectWizardForm(
            request.POST, instance=fb_attr_inst)
        campaign_form = forms.CampaignWizardForm(request.POST)
        if fb_obj_form.is_valid() and campaign_form.is_valid():
            campaign_name = campaign_form.cleaned_data['name']
            filter_feature_layers = []
            enabled_filters = (request.POST.get(
                'enabled-filters-{}'.format(index), '') for index in range(1, 5))
            for inputs in csv.reader(enabled_filters):
                if not inputs:
                    continue

                layer = []
                for feature_string in inputs:
                    feature, operator, value = feature_string.split('.')
                    try:
                        # Go for an existing one
                        ff = relational.FilterFeature.objects.filter(
                            feature=feature, operator=operator, value=value,
                            filter__client=client
                        )[0]
                        ff.pk = None
                    except IndexError:
                        # It'll get saved further down below
                        ff = relational.FilterFeature(
                            feature=feature, operator=operator, value=value
                        )
                    layer.append(ff)
                filter_feature_layers.append(layer)

            root_filter = relational.Filter.objects.create(
                name='{} {} Root Filter'.format(
                    client.name,
                    campaign_name,
                ),
                client=client
            )
            if filter_feature_layers:
                for feature in filter_feature_layers[0]:
                    feature.filter = root_filter
                    feature.save()

                del filter_feature_layers[0]

            root_choiceset = relational.ChoiceSet.objects.create(
                name='{} {} Root ChoiceSet'.format(
                    client.name,
                    campaign_name
                ),
                client=client
            )
            root_choiceset.choicesetfilters.create(
                filter=root_filter)

            choice_sets = [root_choiceset]
            # First layer is the root_choiceset
            for (layer_count, layer) in enumerate(filter_feature_layers, 1):
                for feature in layer:
                    try:
                        cs = choice_sets[layer_count]
                    except IndexError:
                        single_filter = relational.Filter.objects.create(
                            name='{} {}'.format(
                                client.name, campaign_name),
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
                        choice_sets.append(cs)
                    feature.pk = None
                    feature.filter = cs.choicesetfilters.get().filter
                    feature.save()

            fb_obj = relational.FBObject.objects.create(
                name='{} {}'.format(client.name, campaign_name),
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

            # Need to make sure they didn't want a filterless campaign,
            # which would make the empty fallback irrelevant.
            if (campaign_form.cleaned_data['include_empty_fallback'] and
                    root_filter.filterfeatures.exists()):
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
                choice_sets.append(empty_cs)

            last_camp = None
            campaigns = []
            for rank, cs in itertools.izip(reversed(
                    xrange(len(choice_sets))), reversed(choice_sets)):
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
                    fallback_is_cascading=bool(last_camp),
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

    def add_readability( filter ):
        if filter['feature'] == 'gender':
            filter['readable'] = dict(\
                feature = filter['feature'].capitalize(),
                operator = 'is',
                value = filter['value'] )
        elif filter['feature'] == 'age':
            filter['readable'] = dict(
                feature = filter['feature'].capitalize(),
                operator = ':' )
            if filter['operator'] == 'max':
                filter['readable']['value'] = ' '.join( [ filter['value'], 'and younger' ] )
            else:
                filter['readable']['value'] = ' '.join( [ filter['value'], 'and older' ] )
        elif filter['feature'] == 'city' or filter['feature'] == 'state':
            filter['readable'] = dict(
                feature = 'Lives',
                operator = 'in',
                value = filter['value'].replace('||', ', ' )
            )

            if filter['value'].count('||') == 1:
                filter['readable']['value'] = filter['value'].replace('||', ' or ' )
            elif '||' in filter['value']:
                lastComma = filter['readable']['value'].rfind(',')
                filter['readable']['value'] = ' '.join( [
                    filter['readable']['value'][:lastComma+1],
                    'or',
                    filter['readable']['value'][lastComma+2:] ] )
            elif 'new york' in filter['value'].lower():
                filter['readable']['value'] += ' ' + filter['feature']  
        return filter

    
    filter_features = [\
        add_readability(filter) for filter in relational.FilterFeature.objects.filter(
            filter__client=client, feature__isnull=False,
            operator__isnull=False, value__isnull=False)\
                .values('feature', 'operator', 'value').distinct() ]

    return render(request, 'targetadmin/campaign_wizard.html', {
        'client': client,
        'fb_obj_form': fb_obj_form,
        'campaign_form': campaign_form,
        'filter_features': filter_features
    })


@utils.auth_client_required
def campaign_wizard_finish(request, client_pk, campaign_pk, content_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    root_campaign = get_object_or_404(relational.Campaign, pk=campaign_pk)
    properties = root_campaign.campaignproperties.get()
    content = get_object_or_404(relational.ClientContent, pk=content_pk)
    campaigns = [properties]
    while properties.fallback_campaign:
        properties = properties.fallback_campaign.campaignproperties.get()
        campaigns.append(properties)
    return render(request, 'targetadmin/campaign_wizard_finish.html', {
        'campaigns': campaigns,
        'content': content,
        'client': client,
    })
