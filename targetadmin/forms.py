from django import forms

from targetshare.models import relational


class ClientForm(forms.ModelForm):

    class Meta:
        model = relational.Client


class ContentForm(forms.ModelForm):

    class Meta:
        model = relational.ClientContent
        exclude = ('is_deleted', 'delete_dt')
