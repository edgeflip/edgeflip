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

    self.poll = function (fbid, accessToken, response, px3_task_id, px4_task_id, last_call) {
        /* AJAX call to hit /faces endpoint - receives HTML snippet & stuffs in DOM */
        if (response.authResponse) {
            var friends_div = $('#friends_div');
            var progress = $('#progress');
            var your_friends_div = $('#your-friends-here');

            // In test mode, just use the provided test fbid & token for getting faces
            // Note, however, that you're logged into facebook as you, so trying to
            // share with someone else's friends is going to cause you trouble!
            var ajax_fbid = fbid;
            var ajax_token = accessToken;
            if (self.test_mode) {
                console.log('in test mode');
                console.log(self.test_token);
                ajax_fbid = self.test_fbid;
                ajax_token = self.test_token;
            }

            var params = {
                fbid: ajax_fbid,
                token: ajax_token,
                num_face: self.num_face,
                campaign: self.campaignid,
                content: self.contentid,
                px3_task_id: px3_task_id,
                px4_task_id: px4_task_id,
                last_call: last_call
            };
            if (edgeflip.Url.window.query.efobjsrc)
                params.efobjsrc = edgeflip.Url.window.query.efobjsrc;

            $.ajax({
                type: "POST",
                url: '/faces/',
                dataType: 'json',
                data: params,
                error: function() {
                    your_friends_div.show();
                    progress.hide();
                    clearTimeout(self.pollingTimer_);
                    top.location = self.errorURL;
                },
                success: function(data, textStatus, jqXHR) {
                    self.campaignid = data.campaignid;
                    self.contentid = data.contentid;
                    if (data.status === 'waiting') {
                        if (self.pollingTimer_) {
                            if (self.pollingCount_ > 40) {
                                clearTimeout(self.pollingTimer_);
                                self.poll(fbid, accessToken, response, data.px3_task_id, data.px4_task_id, true);
                            } else {
                                self.pollingCount_ += 1;
                                self.pollingTimer_ = setTimeout(function() {
                                    self.poll(fbid, accessToken, response, data.px3_task_id, data.px4_task_id)
                                }, 500);
                            }
                        } else {
                            self.pollingTimer_ = setTimeout(function() {
                                self.poll(fbid, accessToken, response, data.px3_task_id, data.px4_task_id)
                            }, 500);
                        }
                    } else {
                        displayFriendDiv(data.html, jqXHR);
                        clearTimeout(self.pollingTimer_);
                        if (self.debug) {
                            edgeflip.events.record('faces_page_rendered');
                        }
                    }
                }
            });
        }
    };

    return self;
})(edgeflip, jQuery);

function preload(arrayOfImages) {
/* loads a bunch of images
*/
    $(arrayOfImages).each(function () {
        $('<img />').attr('src',this);
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

function displayFriendDiv(data, jqXHR) {
    $('#your-friends-here').html(data);
    $('#your-friends-here').show();
    $('#friends_div').css('display', 'table');
    $('#progress').hide();
    $('#do_share_button').show()
}
