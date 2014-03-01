Map = (function () {
    var defaults = {
        debug: false,
        dataURL: null
    };
    var self = {
        heartbeat: null,
        user: null,
        init: function (options) {
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

            if (self.debug) {
                $(function () {
                    self.heartbeat = new edgeflip.Heartbeat();
                });
            }

            self.user = new edgeflip.User(edgeflip.FB_APP_ID, {
                onAuth: self.poll,
                onAuthFailure: self.authFailure
            });
            self.user.connect();
        },
        authFailure: function () {
            edgeflip.Event.record('auth_fail', {
                complete: function () {
                    alert("Please authorize the application in order to proceed.");
                    self.user.login();
                }
            });
        },
        poll: function (fbid, token, response) {
            if (!response.authResponse) {
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
                            self.display(data.scores);
                            break;
                        default:
                            throw "Bad status: " + data.status;
                    }
                }
            });
        },
        display: function (scores) {
            console.log(scores) // TODO
        }
    };
    return self;
})();
