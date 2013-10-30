from targetadmin import forms
from targetshare.models import relational
from targetadmin.views.base import (
    ClientRelationListView,
    ClientRelationDetailView,
    ClientRelationFormView
)


class FBObjectListView(ClientRelationListView):
    model = relational.FBObject
    object_string = 'Facebook Object'
    detail_url_name = 'fb-obj-detail'
    create_url_name = 'fb-obj-new'


fb_object_list = FBObjectListView.as_view()


class FBObjectDetailView(ClientRelationDetailView):
    model = relational.FBObject
    object_string = 'Facebook Object'
    edit_url_name = 'fb-obj-edit'


fb_object_detail = FBObjectDetailView.as_view()


class FBObjectFormView(ClientRelationFormView):
    form_class = forms.FBObjectAttributeForm
    model = relational.FBObject
    queryset = relational.FBObject.objects.all()
    success_url = 'fb-obj-detail'
    object_string = 'Facebook Object'

    def get_form(self, form_class):
        form_kwargs = self.get_form_kwargs()
        if self.object:
            form_kwargs['instance'] = self.object.fbobjectattribute_set.get()
            form_kwargs['initial'] = {
                'name': self.object.name,
                'description': self.object.description,
                'client': self.object.client,
            }
        else:
            form_kwargs['client'] = self.client
            form_kwargs['initial'] = {
                'og_action': 'support',
                'og_type': 'cause',
            }
        return form_class(**form_kwargs)


fb_object_edit = FBObjectFormView.as_view()
