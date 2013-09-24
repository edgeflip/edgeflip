from django import forms

from targetshare.models import relational


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
    og_description = forms.CharField(
        label='FB Object Description',
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

    description = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = relational.Filter
        exclude = ('is_deleted', 'delete_dt')


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
    faces_url = forms.CharField()
    thanks_url = forms.CharField()
    error_url = forms.CharField()
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

        relational.CampaignFBObjects.objects.create(
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
        self.fields['global_filter'].queryset = self.client.filters.all()
        self.fields['button_style'].queryset = self.client.buttonstyles.all()
        self.fields['choice_set'].queryset = self.client.choicesets.all()
        self.fields['fb_object'].queryset = self.client.fbobjects.all()
        self.fields['generic_fb_object'].queryset = self.client.fbobjects.all()