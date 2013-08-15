import json
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render
from django.http import HttpResponse


@require_GET
def dashboard(request):

    return render(request, 'dashboard.html')


def chartdata(request):
    data = {'monthly_json': 'nothing'}
 
    return HttpResponse(json.dumps(data), content_type="application/json")
