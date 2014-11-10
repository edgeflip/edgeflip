from django import forms
from django.db.models import F

from targetshare.models import relational


class FacesForm(forms.Form):
    """Faces request validation form."""
    fbid = forms.IntegerField(min_value=1)
    token = forms.CharField()
    num_face = forms.IntegerField(min_value=1)
    campaign = forms.ModelChoiceField(
        relational.Campaign.objects.filter(campaignproperties__root_campaign_id=F('campaign_id'))
    )
    content = forms.ModelChoiceField(relational.ClientContent.objects.all())
    last_call = forms.BooleanField(required=False)
    efobjsrc = forms.CharField(required=False)

    def clean(self):
        # Ensure content belongs to client of campaign:
        campaign = self.cleaned_data.get('campaign')
        content = self.cleaned_data.get('content')
        if campaign and content and campaign.client != content.client:
            raise forms.ValidationError(
                "Requested content does not belong to client of requested campaign"
            )
        return self.cleaned_data
