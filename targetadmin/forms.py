from django import forms

from targetshare.models import relational


class ClientForm(forms.ModelForm):

    class Meta:
        model = relational.Client


class ContentForm(forms.ModelForm):

    class Meta:
        model = relational.ClientContent
        exclude = ('is_deleted', 'delete_dt')


class FBObjectAttributeForm(forms.ModelForm):

    name = forms.CharField()
    description = forms.CharField(required=False)

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
        exclude = ('is_deleted', 'delete_dt', 'fb_object')
