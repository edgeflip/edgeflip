from targetadmin.utils import internal
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
    detail_url_name = 'content-detail'
    create_url_name = 'content-new'


content_list = internal(ContentListView.as_view())


class ContentDetailView(ClientRelationDetailView):
    model = relational.ClientContent
    object_string = 'Content'
    edit_url_name = 'content-edit'


content_detail = internal(ContentDetailView.as_view())


class ContentFormView(ClientRelationFormView):
    form_class = forms.ContentForm
    model = relational.ClientContent
    queryset = relational.ClientContent.objects.all()
    success_url = 'content-detail'
    object_string = 'Content'


content_edit = internal(ContentFormView.as_view())
