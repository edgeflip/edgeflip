{% comment %}
JavaScript include template for the Url utility

Use:
    var successURL = new Url("http://www.site.com/?a=b");

{% endcomment %}
var Url = (function() {
    /* Define and return Url class (& nested UrlQuery module) */
    var UrlQuery = {
        parse: function(query) {
            var result = {};
            if (query[0] === '?')
                query = query.substring(1);
            query.split('&').map(function(pair) {
                if (pair) {
                    var keyvalue = pair.split('=', 2).map(function(part) {
                        return decodeURIComponent(part);
                    });
                    result[keyvalue[0]] = keyvalue[1];
                }
            });
            return result;
        },
        unparse: function(query, carryThroughKeys) {
            var queryKey, queryValue, queryString, queryPairs = [];
            for (queryKey in query) {
                if (query.hasOwnProperty(queryKey)) {
                    if (!carryThroughKeys || carryThroughKeys.indexOf(queryKey) !== -1) {
                        queryValue = query[queryKey];
                        if (queryValue) {
                            queryPairs.push([queryKey, queryValue].map(function (value) {
                                return encodeURIComponent(value);
                            }).join('='));
                        }
                    }
                }
            }
            queryString = queryPairs.join('&');
            if (queryPairs.length > 0) {
                queryString = '?' + queryString;
            }
            return queryString;
        }
    };

    var Url = function (url) {
        /* Constructor for Url objects */
        var parser = document.createElement('a');
        var attr, attrs = [
            'protocol', // http:
            'host',     // example.com:3000
            'pathname', // /pathname/
            'hash',     // #hash
        ];
        parser.href = url;
        for (var index = 0; index < attrs.length; index++) {
            attr = attrs[index];
            this[attr] = parser[attr];
        }
        // IE likes to return an invalid ":" for the protocol
        this.protocol = this.protocol == ':' ? '' : this.protocol;
        this.query = UrlQuery.parse(parser.search);
    };
    Url.prototype.hostname = function() {
        return this.host.split(':', 2)[0];
    };
    Url.prototype.port = function() {
        return this.host.split(':', 2)[1];
    };
    Url.prototype.search = function() {
        return UrlQuery.unparse(this.query);
    };
    Url.prototype.href = function() {
        return this.protocol + '//' + this.host + this.pathname + this.search() + this.hash;
    };

    Url.UrlQuery = UrlQuery;
    Url.window = new Url(window.location);

    return Url;
})();
