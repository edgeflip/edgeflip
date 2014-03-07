{{ namespace|default:"var router" }} = (function () {
    /* Exceptions */

    var RouterError = function (message) {
        this.name = 'RouterError';
        this.message = message;
    };
    RouterError.prototype.toString = function () {
        return this.name + ": " + this.message;
    };

    var NoReverseMatch = function () {
        RouterError.apply(this, arguments);
        this.name = 'NoReverseMatch';
    };
    NoReverseMatch.prototype = Object.create(RouterError.prototype);

    /* Helpers */

    var ObjectToString = function (object) {
        var repr = '';
        for (var key in object) {
            if (repr.length !== 0) repr += ', ';
            repr += key + ': ' + object[key];
        }
        return '{' + repr + '}';
    };

    var ArrayToString = function (array) {
        var repr = '';
        if (array.length !== 0) {
            repr = array.reduce(function(first, second) {
                return first + ', ' + second;
            });
        }
        return '[' + repr + ']';
    };

    var interpolate = function (str, params) {
        var key, value, re;
        for (key in params) {
            value = params[key];
            re = new RegExp('\\%\\(' + key + '\\)s');
            str = str.replace(re, value);
        }
        return str;
    };

    var standardNoReverse = function (slug, args, kwargs, failure) {
        return new NoReverseMatch(
            "Reverse for '" + slug +
            "' with arguments " + ArrayToString(args) +
            " and keyword arguments " + ObjectToString(kwargs) +
            " " + failure + "."
        );
    };

    /* Module */

    var self = {
        RouterError: RouterError,
        NoReverseMatch: NoReverseMatch
    };

    {% block router %}
    self.reverse = function (slug) {
        /* Construct the URL path with the given name from the provided arguments.
         *
         *      reverse('index');
         *      reverse('campaign-detail', 6, 35);
         *      reverse('author-books', {author: 'Hemmingway', book: 2});
         */
        if (typeof slug === 'undefined') {
            throw new self.RouterError("Argument 'slug' required");
        }

        // Sanitize optional arguments:
        var args = [], kwargs = null, index, argument;
        for (index in arguments) {
            if (index == 0) continue;
            argument = arguments[index];
            if (argument instanceof Object) {
                if (kwargs === null) {
                    kwargs = argument;
                } else {
                    throw new self.RouterError('Keyword arguments may not be specified twice');
                }
            } else {
                args.push(argument);
            }
        }
        if (kwargs === null) kwargs = {};

        // Look up route:
        var values = self.urls[slug];
        if (typeof values === 'undefined') {
            throw standardNoReverse(slug, args, kwargs, 'not found');
        }

        // Build URL:
        var template = values[0],
            bits = values[1],
            pattern = values[2];
        var data = {}, bit;
        for (index = 0; index < bits.length; index++) {
            bit = bits[index];
            if (index < args.length) {
                data[bit] = args[index];
            } else {
                data[bit] = kwargs[bit];
            }
        }

        var url = interpolate(template, data),
            re = new RegExp(pattern);
        if (!re.test(url)) {
            throw standardNoReverse(slug, args, kwargs, 'failed');
        }
        return url;
    };
    {% endblock %}

    {% block paths %}
    self.urls = {{ paths|safe }};
    {% endblock %}

    return self;
})();
