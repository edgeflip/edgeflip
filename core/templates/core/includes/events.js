{% comment %}
JavaScript include template for recording events

Requires:
    jQuery

Use:
    edgeflip.events.record('heartbeat');

{% endcomment %}
edgeflip.events = (function ($) {
    var self = {
        config: null,
        setConfig: function (options) {
            /* Point events at the given object for global configuration */
            self.config = options;
        }
    };

    self.record = function (eventType, options) {
        options = options || {};
        var globalOptions = self.config || {};
        var fbid = options.fbid ||
                    (options.user && options.user.fbid) ||
                    (globalOptions.user && globalOptions.user.fbid);
        var content;
        if (options.content) {
            content = options.content;
        } else if (edgeflip.FB_APP_NAME ||
                   edgeflip.FB_OBJ_TYPE ||
                   edgeflip.FB_OBJ_URL) {
            content = edgeflip.FB_APP_NAME +
                        ':' + edgeflip.FB_OBJ_TYPE +
                        ' ' + edgeflip.FB_OBJ_URL;
        }

        $.ajax({
            type: 'POST',
            url: "{% url 'targetshare:record-event' %}",
            dataType: 'html',
            data: {
                eventType: eventType,
                userid: fbid,
                content: content,
                campaignid: options.campaignid || globalOptions.campaignid,
                contentid: options.contentid || globalOptions.contentid,
                appid: options.fb_app_id || edgeflip.FB_APP_ID,
                actionid: options.actionid,
                api: options.api,
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

    return self;
})(jQuery);
