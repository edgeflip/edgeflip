from django import forms

from targetshare import classifier
from targetshare.models import relational

from targetadmin.utils import fix_image_url, fix_redirect_url


class ClientForm(forms.ModelForm):

    class Meta:
        model = relational.Client


class ContentForm(forms.ModelForm):

    description = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = relational.ClientContent
        exclude = ('is_deleted', 'delete_dt')


class FBObjectAttributeForm(forms.ModelForm):

    name = forms.CharField()
    description = forms.CharField(required=False, widget=forms.Textarea)
    sharing_prompt = forms.CharField(label="Headline")
    sharing_sub_header = forms.CharField(
        label="Sub-Header",
        required=False,
        widget=forms.Textarea
    )
    og_description = forms.CharField(
        label='Facebook post Description',
        required=False,
        widget=forms.Textarea
    )

    def save(self, commit=True):
        fb_obj_attr = super(FBObjectAttributeForm, self).save(False)
        if commit:
            if not fb_obj_attr.fb_object:
                fb_obj = relational.FBObject.objects.create(
                    name=self.cleaned_data['name'],
                    description=self.cleaned_data['description'],
                    client=self.client
                )
                fb_obj_attr.fb_object = fb_obj
            else:
                fb_obj = fb_obj_attr.fb_object
                fb_obj.name = self.cleaned_data['name']
                fb_obj.description = self.cleaned_data['description']
                fb_obj.save()

            fb_obj_attr.save()
        return fb_obj_attr.fb_object

    def __init__(self, client=None, *args, **kwargs):
        super(FBObjectAttributeForm, self).__init__(*args, **kwargs)
        self.client = client

    class Meta:
        model = relational.FBObjectAttribute
        exclude = ('is_deleted', 'delete_dt', 'fb_object', 'end_dt',)


class FilterForm(forms.ModelForm):

    name = forms.CharField(required=True)

    class Meta:
        model = relational.Filter
        exclude = ('is_deleted', 'delete_dt', 'client')


class WizardFilterFeatureForm(forms.ModelForm):

    CHOICES = (
        ('', 'Select Filter Type'),
        ('age', 'Age'),
        ('gender', 'Gender'),
        ('location', 'Location'),
        ('interest', 'Interest'),
    )

    TOPICS = sorted(classifier.SIMPLE_WEIGHTS)
    feature = forms.ChoiceField(
        label='Filter Type',
        choices=CHOICES )

    class Meta(object):
        model = relational.FilterFeature
        exclude = ('end_dt', 'value_type', 'feature_type', 'filter')


class FilterFeatureForm(forms.ModelForm):
    ''' This class should really be deprecated along with the direct editing
    of filters view that it belongs to. Then again, maybe that serves a
    real purpose that justifies keeping it, food for thought
    '''

    CHOICES = (
        ('', 'Select Filter Type'),
        ('age', 'Age'),
        ('location', 'Location'),
        ('gender', 'Gender'),
        # For the direct Filter editing forms
        ('city', 'City'),
        ('state', 'State'),
    )

    feature = forms.ChoiceField(choices=CHOICES)

    class Meta:
        model = relational.FilterFeature
        exclude = ('end_dt', 'value_type', 'feature_type', 'filter')


class ChoiceSetForm(forms.ModelForm):

    description = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = relational.ChoiceSet
        exclude = ('is_deleted', 'delete_dt')


class ButtonStyleForm(forms.ModelForm):

    name = forms.CharField()
    description = forms.CharField(required=False, widget=forms.Textarea)

    def save(self, commit=True):
        bsf = super(ButtonStyleForm, self).save(False)
        if commit:
            if not bsf.button_style:
                button = relational.ButtonStyle.objects.create(
                    name=self.cleaned_data['name'],
                    description=self.cleaned_data['description'],
                    client=self.client
                )
                bsf.button_style = button
            else:
                button = bsf.button_style
                button.name = self.cleaned_data['name']
                button.description = self.cleaned_data['description']
                button.save()

            bsf.save()
        return bsf.button_style

    def __init__(self, client=None, *args, **kwargs):
        super(ButtonStyleForm, self).__init__(*args, **kwargs)
        self.client = client

    class Meta:
        model = relational.ButtonStyleFile
        exclude = ('button_style', 'end_dt')


class CampaignForm(forms.Form):

    name = forms.CharField()
    description = forms.CharField(required=False, widget=forms.Textarea)
    faces_url = forms.CharField(
        label='Host URL',
        help_text='Provide the URL where this campaign will be embedded. '
                  'Leave blank if using Facebook canvas'
    )
    thanks_url = forms.CharField(
        label='Post-Share URL',
        help_text='This is the URL users get sent to after they share. '
                  'This is usually a thank you page or a secondary ask.'
    )
    error_url = forms.CharField(
        label='Sharing Error URL',
        help_text='If the user does not have any friends that fit the '
                  'targeting criteria or if there is a sharing error, '
                  'they will be sent to this URL'
    )
    fallback_campaign = forms.ModelChoiceField(
        queryset=relational.Campaign.objects.none(),
        required=False
    )
    fallback_content = forms.ModelChoiceField(
        queryset=relational.ClientContent.objects.none(),
        required=False
    )
    cascading_fallback = forms.BooleanField(required=False)
    min_friends_to_show = forms.IntegerField()
    global_filter = forms.ModelChoiceField(
        queryset=relational.Filter.objects.none()
    )
    button_style = forms.ModelChoiceField(
        queryset=relational.ButtonStyle.objects.none(),
        required=False
    )
    choice_set = forms.ModelChoiceField(
        queryset=relational.ChoiceSet.objects.none(),
        required=False
    )
    allow_generic = forms.BooleanField(required=False)
    generic_url_slug = forms.CharField(required=False)
    generic_fb_object = forms.ModelChoiceField(
        queryset=relational.FBObject.objects.none(),
        required=False,
    )
    fb_object = forms.ModelChoiceField(
        queryset=relational.FBObject.objects.none()
    )

    def clean_generic_fb_object(self):
        gen_fb_obj = self.cleaned_data.get('generic_fb_object')
        if self.cleaned_data.get('allow_generic') and not gen_fb_obj:
            raise forms.ValidationError(
                'Generic FB Object not selected, but Allow Generic specified as True'
            )
        else:
            return gen_fb_obj

    def save(self):
        ''' Currently only supports creating, not editing, campaigns '''
        data = self.cleaned_data
        campaign = relational.Campaign.objects.create(
            name=data.get('name'),
            description=data.get('description'),
            client=self.client
        )
        campaign.save()

        # Get all of our related objects together
        properties = relational.CampaignProperties(campaign=campaign)
        choice_set = relational.CampaignChoiceSet(campaign=campaign)
        button_style = relational.CampaignButtonStyle(campaign=campaign)
        global_filter = relational.CampaignGlobalFilter(campaign=campaign)

        # Campaign Properties
        properties.client_faces_url = data.get('faces_url')
        properties.client_thanks_url = data.get('thanks_url')
        properties.client_error_url = data.get('error_url')
        properties.fallback_campaign = data.get('fallback_campaign')
        properties.fallback_content = data.get('fallback_content')
        properties.fallback_is_cascading = data.get('cascading_fallback', False)
        properties.min_friends = data.get('min_friends_to_show')
        properties.save()

        # Global Filter
        global_filter.filter = data.get('global_filter')
        global_filter.rand_cdf = 1.0
        global_filter.save()

        # Button Style
        button_style.button_style = data.get('button_style')
        button_style.rand_cdf = 1.0
        button_style.save()

        # Choice Set
        choice_set.choice_set = data.get('choice_set')
        choice_set.allow_generic = data.get('allow_generic', False)
        choice_set.generic_url_slug = data.get('generic_url_slug')
        choice_set.rand_cdf = 1.0
        choice_set.save()

        # FB Objects
        if data.get('generic_fb_object'):
            relational.CampaignGenericFBObjects.objects.create(
                campaign=campaign,
                fb_object=data.get('generic_fb_object'),
                rand_cdf=1.0
            )

        relational.CampaignFBObject.objects.create(
            campaign=campaign,
            filter=data.get('global_filter'),
            fb_object=data.get('fb_object'),
            rand_cdf=1.0
        )

        return campaign

    def __init__(self, client, *args, **kwargs):
        super(CampaignForm, self).__init__(*args, **kwargs)
        self.client = client
        self.fields['fallback_campaign'].queryset = self.client.campaigns.all()
        self.fields['fallback_content'].queryset = self.client.clientcontent.all()
        self.fields['global_filter'].queryset = self.client.filters.all()
        self.fields['button_style'].queryset = self.client.buttonstyles.all()
        self.fields['choice_set'].queryset = self.client.choicesets.all()
        self.fields['fb_object'].queryset = self.client.fbobjects.all()
        self.fields['generic_fb_object'].queryset = self.client.fbobjects.all()


# Wizard Forms
class CampaignWizardForm(forms.Form):

    name = forms.CharField(
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )

    faces_url = forms.CharField(
        required=False,
        label='Host URL (optional)'
    )
    error_url = forms.CharField(
        label='Error URL'
    )
    thanks_url = forms.CharField(
        label='Thanks URL'
    )
    content_url = forms.CharField(
        label='Content URL'
    )

    include_empty_fallback = forms.BooleanField(
        help_text=(
            'Some users will not have enough friends who fit the targeting '
            'criteria. Checking this box will fill in the friend suggestions '
            'with friends that do not fit the targeting criteria but are '
            'still influenceable. You should check this box if you would '
            'rather reach more people than those strictly in your targeting '
            'criteria.'
        ),
        initial=True,
        required=False
    )

    def clean_content_url(self):
        return fix_redirect_url(self.cleaned_data['content_url'], 'http')

    def clean_error_url(self):
        return fix_redirect_url(self.cleaned_data['error_url'], 'http')

    def clean_thanks_url(self):
        return fix_redirect_url(self.cleaned_data['thanks_url'], 'http')


class FBObjectWizardForm(forms.ModelForm):

    og_description = forms.CharField(
        label='Facebook post description',
        required=False,
        widget=forms.Textarea
    )
    og_title = forms.CharField(label='Facebook post title')
    og_image = forms.CharField(label='Facebook post image URL')
    org_name = forms.CharField(
        label='Cause or organization being supported'
    )
    msg1_pre = forms.CharField(
        required=False,
        label='Text before friend names (optional)'
    )
    msg1_post = forms.CharField(
        required=False,
        label='Text after friend names (optional)'
    )
    msg2_pre = forms.CharField(
        required=False,
        label='Text Before Friend Names (optional)'
    )
    msg2_post = forms.CharField(
        required=False,
        label='Text After Friend Names (optional)'
    )
    sharing_prompt = forms.CharField(label="Headline")
    sharing_sub_header = forms.CharField(
        label="Sub-header (optional)",
        required=False,
        widget=forms.Textarea
    )

    def clean_og_image(self):
        og_image = self.cleaned_data['og_image']
        return fix_image_url(og_image)

    class Meta:
        model = relational.FBObjectAttribute
        exclude = (
            'fb_object', 'og_action', 'og_type', 'page_title',
            'url_slug', 'end_dt'
        )


class SnippetModelChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return u'{} - {}'.format(obj.pk, obj.name)


class SnippetForm(forms.Form):

    campaign = SnippetModelChoiceField(
        queryset=relational.Campaign.objects.none()
    )
    content = SnippetModelChoiceField(
        queryset=relational.ClientContent.objects.none()
    )

    def __init__(self, client, *args, **kwargs):
        super(SnippetForm, self).__init__(*args, **kwargs)
        self.fields['campaign'].queryset = client.campaigns.exclude(
            rootcampaign_properties=None
        )
        self.fields['content'].queryset = client.clientcontent.all()
