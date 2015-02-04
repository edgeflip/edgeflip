edgeflip.faces = (function (edgeflip, $) {
    var self = {
        pollingTimer_: null,
        pollingCount_: 0
    };

    self.init = function (options) {
        options = options || {};
        self.debug = options.debug;
        self.test_mode = options.test_mode;
        self.thanksURL = options.thanksURL;
        self.errorURL = options.errorURL;
        self.api = options.api;
        self.campaignid = options.campaignid;
        self.contentid = options.contentid;
        self.num_face = options.num_face || 9;
        self.max_face = 10;
        self.test_fbid = self.test_mode ? options.test_fbid : null;
        self.test_token = self.test_mode ? options.test_token : null;

        if (options.user) {
            self.user = options.user;
        } else {
            self.user = new edgeflip.User(
                edgeflip.FB_APP_ID, {
                    api: self.api,
                    loginScope: options.loginScope,
                    onConnect: self.poll,
                    onAuthFailure: authFailure
                }
            );
        }

        // Instruct events.record to check faces for campaignid & contentid:
        edgeflip.events.setConfig(self);

        if (self.debug) {
            // Start heartbeat as soon as DOM ready:
            $(function () {
                self.heartbeat = new edgeflip.Heartbeat();
            });
        } else {
            self.heartbeat = null;
        }
    };

    self.poll = function (fbid, accessToken, response, last_call) {
        /* Perform an asynchronous HTTP call to the "faces" endpoint.
         *
         * On success, receives an HTML snippet & stuffs it in the DOM.
         */
        if (!response.authResponse) {
            return;
        }

        if (self.test_mode) {
            // In test mode, just use the provided test fbid & token for getting faces
            // Note, however, that you're logged into facebook as you, so trying to
            // share with someone else's friends is going to cause you trouble!
            console.log('in test mode:', self.test_token);
        }

        if (!self.pollingTimer_) {
            updateProgressBar(5);
        }

        $.ajax({
            type: 'POST',
            url: '/faces/',
            dataType: 'json',
            data: {
                fbid: self.test_mode ? self.test_fbid : fbid,
                token: self.test_mode ? self.test_token : accessToken,
                num_face: self.num_face,
                api: self.api,
                campaign: self.campaignid,
                content: self.contentid,
                last_call: last_call,
                efobjsrc: edgeflip.Url.window.query.efobjsrc
            },
            success: function (data) {
                var nextPoll;

                self.campaignid = data.campaignid;
                self.contentid = data.contentid;

                if (data.status === 'waiting') {
                    // Continue polling
                    nextPoll = self.poll.bind(undefined, fbid, accessToken, response);

                    if (self.pollingCount_ > 40) {
                        // Give it one last call:
                        clearTimeout(self.pollingTimer_);
                        nextPoll(true);
                        return;
                    }

                    if (self.pollingTimer_) self.pollingCount_ ++;
                    updateProgressBar(Math.floor((2 * self.pollingCount_) + 10));
                    self.pollingTimer_ = setTimeout(nextPoll, 500);
                    return;
                }

                // Success!
                updateProgressBar(100);
                setTimeout(function () {
                    displayFriendDiv(data.html);
                    updateProgressBar(0);
                }, 500);
                clearTimeout(self.pollingTimer_);
                if (self.debug) {
                    edgeflip.events.record('faces_page_rendered');
                }
            },
            error: function () {
                $('#your-friends-here').show();
                $('#progress').hide();
                clearTimeout(self.pollingTimer_);
                edgeflip.util.outgoingRedirect(self.errorURL);
            }
        });
    };

    return self;
})(edgeflip, jQuery);


function updateProgressBar( percent ) {
    if ($('#spinner').css('background-image') != 'none') {
        return;
    }

    if (percent > 100) {
        percent = 100;
    }

    $('#progress-text span').width(percent + '%');
};


function preload(arrayOfImages) {
    /* loads a bunch of images
    */
    $(arrayOfImages).each(function () {
        $('<img />').attr('src', this);
    });
}

function authFailure() {
    $('#your-friends-here').html(
        '<p id="reconnect_text">Please authorize the application in order to proceed.</p><div id="reconnect_button" class="button_big button_active" onclick="edgeflip.faces.user.login();">Connect</div>'
    );
    $('#progress').hide();
    $('#friends_div').css('display', 'table');
    edgeflip.events.record('auth_fail');
    $('#reconnect_button').click(function(){
        $('#progress').show();
        $('#reconnect_button').hide();
        $('#reconnect_text').hide();
    });
}

function displayFriendDiv(data) {
    $('#progress').hide();
    $('body').addClass('faces');
    $('#your-friends-here').html(data);
    $('#your-friends-here').show();
    $('#friends_div').css('display', 'table');
    $('#do_share_button').show();
}
