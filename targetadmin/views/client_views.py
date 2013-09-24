from targetadmin.utils import internal
from targetadmin import forms
from targetshare.models import relational
from targetadmin.views.base import CRUDView


class ClientFormView(CRUDView):
    template_name = 'targetadmin/client_edit.html'
    form_class = forms.ClientForm
    success_url = 'client-detail'
    queryset = relational.Client.objects.all()

client_view = internal(ClientFormView.as_view())
