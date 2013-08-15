import json
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render

@require_GET
def dashboard(request):

    return render(request, 'dashboard.html')


@require_POST
def chartdata(request):
    
    return json.dumps({'reponse':'woo'})
