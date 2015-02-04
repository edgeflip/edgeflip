{% comment %}
JavaScript include template for the util module

Use:
    edgeflip.util.outgoingRedirect("http://www.site.com/?a=b");

{% endcomment %}
edgeflip.util = {
    outgoingRedirect: function (url) {
        var origin, redirectUrl = url;
        if (/^\/([^\/]|$)/.test(url)) {
            /* The "URL" begins with a single forward slash;
            * treat it as a full path.
            * Most browsers understand what we "mean", that the top frame's
            * URL should be thanksURL relative to our context; but,
            * understandably, IE does not.
            */
            // Nor does IE support location.origin:
            origin = window.location.protocol + '//' + window.location.host;
            redirectUrl = origin + url;
        }
        top.location = redirectUrl;
    }
};
