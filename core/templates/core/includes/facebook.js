{% comment %}
JavaScript include template for interacting with Facebook

Requires:
    jQuery
    recordEvent

Use:
    user = FBUser('<FB_APP_ID>', {onAuth: reportBack});

{% endcomment %}
var FBUser = function (fbAppId, options) {
    options = options || {};
    var self = this;

    // Init object context:
    self.fbid = null;
    self.token = null;
    self.fbAppId = fbAppId;
    self.rootId = options.rootId || 'fb-root';
    self.onAuth = options.onAuth;
    self.onAuthFailure = options.onAuthFailure;
};

FBUser.prototype.connect = function () {
    var self = this;
    window.fbAsyncInit = self.fbAsyncInit.bind(self); // where FB looks
    $(self.fbAsyncLoad.bind(self)); // on ready
};

FBUser.prototype.fbAsyncLoad = function () {
    var rootSelector = '#' + this.rootId;
    var apiSrc = document.location.protocol 
        + '//connect.facebook.net/en_US/all.js';
    var scriptSelector = 'script[src="' + apiSrc + '"]';
    if ($(rootSelector).length === 0) {
        $('body').append('<div id="' + this.rootId + '"></div>');
    }
    if ($(rootSelector).find(scriptSelector).length === 0) {
        var e = document.createElement('script');
        e.async = true;
        e.src = apiSrc;
        document.getElementById(this.rootId).appendChild(e);
    }
};

FBUser.prototype.fbAsyncInit = function () {
    var self = this;

    FB.init({
        appId: self.fbAppId,
        status: true,
        cookie: true,
        xfbml: true,
        oauth: true
    });

    FB.Event.subscribe('auth.statusChange', function(response) {
        if (response.status === 'connected') {
            self.fbid = response.authResponse.userID;
            self.token = response.authResponse.accessToken;
            recordEvent('authorized', {
                fbid: self.fbid,
                fb_app_id: self.fbAppId,
                content: '',
                friends: [],
                token: self.token
            });
            if (self.onAuth) {
                self.onAuth(self.fbid, self.token, response);
            }
        } else {
            // User isn't logged in or hasn't authed, so try doing the login directly
            // (note: if we wanted to detect logged in to FB but not authed, could use status==='not_authorized')
            self.login();
        }
    });
};

FBUser.prototype.login = function () {
    /* pops up facebook's signin page in a _top window */
    var self = this;
    FB.login(function(response) {
        if (response.status !== 'connected' && self.onAuthFailure) {
            self.onAuthFailure();
        }
    }, {scope:'read_stream,user_photos,friends_photos,email,user_birthday,friends_birthday,user_about_me,user_location,friends_location,user_likes,friends_likes,user_interests,friends_interests'});
};
