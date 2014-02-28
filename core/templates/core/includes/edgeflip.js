{% comment %}
JavaScript include template for the edgeflip namespace

Use:
    edgeflip.FB_APP_ID
    edgeflip.MyObject...

{% endcomment %}
if (typeof edgeflip === 'undefined') {
    var edgeflip = {
        FB_APP_ID: null,
        FB_APP_NAME: null,
        FB_ACTION_TYPE: null,
        FB_OBJ_TYPE: null,
        FB_OBJ_URL: null
    };
}
