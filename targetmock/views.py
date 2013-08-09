from django.http import HttpResponseNotFound
from django.shortcuts import render

DEFAULT_EF_URL = 'http://local.edgeflip.com:8080'

## random blob of data we need - per state info
state_sen_info = {
    'CA': {
        'email': 'fb@senate.gov',
        'name': 'Fozzie Bear',
        'phone': '415-555-1212',
        'state_name': 'California'
    },
    'EC': {
        'email': 'smokestax@senate.gov',
        'name': 'Smokestax',
        'phone': '202-123-4567',
        'state_name': 'East Calihio'
    },
    'IL': {
        'email': 'rowlf@senate.gov',
        'name': 'Rowlf The Dog',
        'phone': '312-555-1212',
        'state_name': 'Illinois'
    },
    'MA': {
        'email': 'kermit@senate.gov',
        'name': 'Kermit The Frog',
        'phone': '617-867-5309',
        'state_name': 'Massachusetts'
    },
    'NY': {
        'email': 'misspig@senate.gov',
        'name': 'Miss Piggy',
        'phone': '212-555-1212',
        'state_name': 'New York'
    }
}


def ofa_landing(request):
    """lives on client site - where ofa_climate redirects to"""
    state = request.GET.get('state')
    if not state:
        return HttpResponseNotFound('No State Specified')

    sen_info = state_sen_info.get(state)
    if (not sen_info):
        return HttpResponseNotFound('No targets in that state.')
    page_title = "Tell Sen. %s We're Putting Denial on Trial!" % sen_info['name']
    return render(request, 'targetmock/ofa_climate_landing.html', {
        'sen_info': sen_info,
        'page_title': page_title,
    })
