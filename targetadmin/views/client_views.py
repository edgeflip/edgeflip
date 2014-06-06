from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.shortcuts import redirect

from targetadmin import forms, utils
from targetshare.models import relational
from targetadmin.views.base import CRUDView


class ClientListView(ListView):
    model = relational.Client,
    template_name = 'targetadmin/home.html'
    queryset = relational.Client.objects.all()

    def render_to_response(self,context,**response_kwargs):
        if len( context['client_list'] ) == 1: 
            return redirect( 'targetadmin:client-detail', context['client_list'][0].pk )
        else:
            return ListView.render_to_response( self, context, **response_kwargs) 

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
    pk_url_kwarg = 'client_pk'
  
    def get_template_names(self):
        return [ 'targetadmin/superuser_home.html' ] if self.request.user.is_superuser\
             else [ 'targetadmin/client_home.html' ]

    def get_context_data(self,**kwargs):
        context = super(ClientDetailView, self).get_context_data(**kwargs)
        context['root_campaigns'] = context['client'].campaigns\
            .exclude(rootcampaign_properties=None)\
            .order_by( '-create_dt' )
        return context


class ClientFormView(CRUDView):
    template_name = 'targetadmin/client_edit.html'
    form_class = forms.ClientForm
    success_url = 'targetadmin:client-detail'
    queryset = relational.Client.objects.all()

client_list_view = login_required(ClientListView.as_view(), login_url='targetadmin:login')
client_detail_view = utils.auth_client_required(ClientDetailView.as_view())
client_form_view = ClientFormView.as_view()
