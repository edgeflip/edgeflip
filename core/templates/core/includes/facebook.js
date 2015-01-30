{% comment %}
JavaScript include template for interacting with Facebook

Requires:
    jQuery
    edgeflip.events

Use:
    user = new edgeflip.User(<FB_APP_ID>, {onConnect: reportBack});
    user.connect();

{% endcomment %}
edgeflip.User = function (fbAppId, options) {
    options = options || {};
    this.fbid = null;
    this.token = null;
    this.fbAppId = fbAppId;
    this.rootId = options.rootId || 'fb-root';
    this.onConnect = options.onConnect;
    this.onAuthFailure = options.onAuthFailure;
    this.loginScope = options.loginScope || 'read_stream,user_photos,friends_photos,email,user_birthday,friends_birthday,user_about_me,user_location,friends_location,user_likes,friends_likes,user_interests,friends_interests';
};

edgeflip.User.prototype.connect = function () {
    /* Connect, auth & attempt login */
    window.fbAsyncInit = this.initAuth.bind(this); // where FB looks for init
    $(this.loadFb.bind(this)); // load on ready
};

edgeflip.User.prototype.connectNoAuth = function (fbid, token) {
    /* Connect to Facebook without attempting any auth */
    if (!fbid || !token) {
        throw "connectNoAuth: 'fbid' and 'token' required";
    }
    var self = this;
    self.fbid = fbid;
    self.token = token;
    window.fbAsyncInit = function () {
        FB.init({
            appId: self.fbAppId,
            status: true,
            cookie: true,
            xfbml: true,
            oauth: true
        });
        if (self.onConnect) {
            self.onConnect(self.fbid, self.token);
        }
    };
    $(self.loadFb.bind(self));
};

edgeflip.User.prototype.loadFb = function () {
    /* Load FB API */
    var rootSelector = '#' + this.rootId;
    var apiSrc = document.location.protocol +
        '//connect.facebook.net/en_US/all.js';
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

edgeflip.User.prototype.initAuth = function () {
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
            edgeflip.events.record('authorized', {
                fbid: self.fbid,
                fb_app_id: self.fbAppId,
                content: '',
                friends: [],
                token: self.token
            });
            if (self.onConnect) {
                self.onConnect(self.fbid, self.token, response);
            }
        } else {
            // User isn't logged in or hasn't authed, so try doing the login directly
            // (NOTE: If we wanted to detect logged in to FB but not authed,
            // could use status==='not_authorized')
            self.login();
        }
    });
};

edgeflip.User.prototype.login = function () {
    /* pops up facebook's signin page in a _top window */
    var self = this;
    FB.login(function(response) {
        if (response.status !== 'connected' && self.onAuthFailure) {
            self.onAuthFailure();
        }
    }, {scope: self.loginScope});
};
