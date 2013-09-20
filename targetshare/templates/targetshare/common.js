{% comment %} NOTE: parent template is responsible for loading jQuery {% endcomment %}

// Django CSRF magic
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

var sessionid = '{{ session_id }}';
var campaignid = {{ campaign.pk }};
var contentid = {{ content.pk }};
var content = '{{ fb_params.fb_app_name }}:button {{ goto|safe }}';
var appid = {{ fb_params.fb_app_id }};

function recordEvent(eventType, fbid, redirect, accessToken) {


    var params = {
        userid: fbid,
        appid: appid,
        content: content,
        eventType: eventType,
        sessionid: sessionid,
        campaignid: campaignid,
        contentid: contentid,
        token: accessToken
    };

    $.ajax({
        type: "POST",
        url: "{% url 'record-event' %}",
        dataType: 'html',
        data: params,
        error: function(jqXHR, textStatus, errorThrown) {
            // Even if the event writing failed, still send the user on their way...
            if (redirect) {
                top.location = redirect;
            }
        },
        success: function(data, textStatus, jqXHR) {
            var header_efsid = jqXHR.getResponseHeader('X-EF-SessionID');
            sessionid = header_efsid || sessionid;
            if (redirect) {
                top.location = redirect;
            }
        }
    });

}

