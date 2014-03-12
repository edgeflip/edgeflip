from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView

from targetadmin import forms, utils
from targetshare.models import relational
from targetadmin.views.base import CRUDView


class ClientListView(ListView):
    model = relational.Client,
    template_name = 'targetadmin/home.html'
    queryset = relational.Client.objects.all()

    def get_queryset(self):
        queryset = super(ClientListView, self).get_queryset()
        if self.request.user.is_superuser:
            return queryset
        else:
            return queryset.filter(
                auth_groups__user=self.request.user
            ).distinct()


class ClientDetailView(DetailView):
    model = relational.Client
    template_name = 'targetadmin/client_home.html'
    pk_url_kwarg = 'client_pk'


class ClientFormView(CRUDView):
    template_name = 'targetadmin/client_edit.html'
    form_class = forms.ClientForm
    success_url = 'targetadmin:client-detail'
    queryset = relational.Client.objects.all()

client_list_view = login_required(ClientListView.as_view(), login_url='login')
client_detail_view = utils.auth_client_required(ClientDetailView.as_view())
client_form_view = ClientFormView.as_view()
