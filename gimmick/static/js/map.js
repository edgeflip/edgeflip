edgeflip.map = (function (edgeflip, $) {
    var defaults = {
        debug: false,
        dataURL: null,
        header: ['State', 'Value'],
        test: null
    };

    var self = {
        heartbeat: null,
        user: null,
        chart: null,
        scores: null,
        totalScore: null
    };

    self.init = function (options) {
        options = options || {};
        var property, givenValue, defaultValue;
        for (property in defaults) {
            givenValue = options[property];
            defaultValue = defaults[property];
            if (typeof givenValue === 'undefined') {
                self[property] = defaultValue;
            } else {
                self[property] = givenValue;
            }
        }

        self.user = new edgeflip.User(
            edgeflip.FB_APP_ID, {
                onConnect: self.poll,
                onAuthFailure: self.authFailure
            }
        );

        $(function () {
            if (self.debug) {
                self.heartbeat = new edgeflip.Heartbeat();
            }

            if (self.test) {
                self.user.connectNoAuth(self.test.fbid, self.test.token);
            } else {
                self.user.connect();
            }

            var output = document.getElementById('map');
            self.chart = new google.visualization.GeoChart(output);
            self.draw();
        });
    };

    self.authFailure = function () {
        edgeflip.events.record('auth_fail', {
            complete: function () {
                alert("Please authorize the application in order to proceed.");
                self.user.login();
            }
        });
    };

    self.poll = function (fbid, token, response) {
        if (!self.test && !response.authResponse) {
            throw "Authentication failure";
        }
        $.ajax({
            type: 'POST',
            url: self.dataURL,
            dataType: 'json',
            data: {
                fbid: fbid,
                token: token
            },
            error: function () {
                alert("No results"); // FIXME
            },
            success: function (data) {
                switch (data.status) {
                    case 'waiting':
                        setTimeout(function () {
                            self.poll(fbid, token, response);
                        }, 500);
                        break;
                    case 'success':
                        self.scores = data.scores;
                        self.totalScore = totalScore(self.scores);
                        self.scores.unshift(self.header);
                        self.displayScores();
                        break;
                    default:
                        throw "Bad status: " + data.status;
                }
            }
        });
    };

    self.draw = function (values, options) {
        values = values || [self.header];
        options = options || {
            region: 'US',
            resolution: 'provinces'
        };
        var data = google.visualization.arrayToDataTable(values);
        self.chart.draw(data, options);
    };

    self.displayScores = function () {
        self.draw(self.scores);
        $('#total-score').text(self.totalScore);
    };

    // TODO: consider calculation
    var totalScore = function (scores) {
        var score = 0;
        for (var index = 0; index < scores.length; index++) {
            score += scores[index][1];
        }
        return Math.round(score);
    };

    return self;
})(edgeflip, jQuery);
