from targetadmin import forms
from targetshare.models import relational
from targetadmin.views.base import (
    ClientRelationListView,
    ClientRelationDetailView,
    ClientRelationFormView
)


class ContentListView(ClientRelationListView):
    model = relational.ClientContent
    object_string = 'Content'
    detail_url_name = 'targetadmin:content-detail'
    create_url_name = 'targetadmin:content-new'


content_list = ContentListView.as_view()


class ContentDetailView(ClientRelationDetailView):
    model = relational.ClientContent
    object_string = 'Content'
    edit_url_name = 'targetadmin:content-edit'


content_detail = ContentDetailView.as_view()


class ContentFormView(ClientRelationFormView):
    form_class = forms.ContentForm
    model = relational.ClientContent
    queryset = relational.ClientContent.objects.all()
    success_url = 'targetadmin:content-detail'
    object_string = 'Content'


content_edit = ContentFormView.as_view()
