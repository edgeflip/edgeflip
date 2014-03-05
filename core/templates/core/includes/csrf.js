{% comment %}
JavaScript include template for ensuring inclusion of CSRF headers in jQuery AJAX

Requires:
    jQuery

Use:
    <body>
    {% csrf_token %}
    <script>edgeflip.csrf.setHeader();</script>
    ...

{% endcomment %}
edgeflip.csrf = (function ($) {
    var self = {
        retrieveFromCookie: function (name) {
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
        },
        safeMethod: function (method) {
            // these HTTP methods do not require CSRF protection
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        },
        setHeader: function () {
            var csrftoken = self.retrieveFromCookie('csrftoken');
            $.ajaxSetup({
                crossDomain: false, // obviates need for sameOrigin test
                beforeSend: function(xhr, settings) {
                    if (!self.safeMethod(settings.type)) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            });
        }
    };
    return self;
})(jQuery);
