from django import forms

from targetshare.models import relational


class ClientForm(forms.ModelForm):

    class Meta:
        model = relational.Client
