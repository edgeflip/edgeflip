from targetadmin import forms
from targetadmin.views.base import (
    ClientRelationListView,
    ClientRelationDetailView,
    ClientRelationFormView
)
from targetshare.models import relational


class ButtonListView(ClientRelationListView):
    model = relational.ButtonStyle
    object_string = 'Button Style'
    detail_url_name = 'targetadmin:button-detail'
    create_url_name = 'targetadmin:button-new'


button_list = ButtonListView.as_view()


class ButtonDetailView(ClientRelationDetailView):
    model = relational.ButtonStyle
    object_string = 'Button Style'
    edit_url_name = 'targetadmin:button-edit'


button_detail = ButtonDetailView.as_view()


class ButtonFormView(ClientRelationFormView):
    form_class = forms.ButtonStyleForm
    model = relational.ButtonStyle
    queryset = relational.ButtonStyle.objects.all()
    success_url = 'targetadmin:button-detail'
    object_string = 'Button Style'

    def get_form(self, form_class):
        form_kwargs = self.get_form_kwargs()
        if self.object:
            form_kwargs['instance'] = self.object.buttonstylefiles.get()
            form_kwargs['initial'] = {
                'name': self.object.name,
                'description': self.object.description,
                'client': self.object.client
            }
        else:
            form_kwargs['client'] = self.client
        return form_class(**form_kwargs)


button_edit = ButtonFormView.as_view()
