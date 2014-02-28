{% comment %}
JavaScript include template for the recording events

Requires:
    jQuery

Use:
    recordEvent('heartbeat');

{% endcomment %}
var recordEvent = function (eventType, options) {
    options = options || {};

    // Support globals in frame_faces.html:
    var fbid = typeof user !== 'undefined' ? user.fbid : null;
    var campid = typeof campaignid !== 'undefined' ? campaignid : null;
    var contid = typeof contentid !== 'undefined' ? contentid : null;

    // and other global settings:
    var fb_app_id = typeof FB_APP_ID !== 'undefined' ? FB_APP_ID : '';
    var fb_app_name = typeof FB_APP_NAME !== 'undefined' ? FB_APP_NAME : '';
    var fb_obj_type = typeof FB_OBJ_TYPE !== 'undefined' ? FB_OBJ_TYPE : '';
    var fb_obj_url = typeof FB_OBJ_URL !== 'undefined' ? FB_OBJ_URL : '';

    $.ajax({
        type: 'POST',
        url: "{% url 'record-event' %}",
        dataType: 'html',
        data: {
            eventType: eventType,
            userid: options.fbid || fbid,
            campaignid: options.campaignid || campid,
            contentid: options.contentid || contid,
            appid: options.fb_app_id || fb_app_id,
            content: options.content || fb_app_name + ':' + fb_obj_type + ' ' + fb_obj_url,
            actionid: options.actionid,
            token: options.token,
            friends: options.friends,
            shareMsg: options.shareMsg,
            errorMsg: options.errorMsg
        },
        error: options.error,
        success: options.success,
        complete: options.complete
    });
};
