edgeflip.engage = (function (edgeflip, $) {
    // Attributes (non)-optionally set by user via init():
    var Required = new Object(),
        defaults = {
            dataURL: null, // set lazily
            taskId: Required
        };

    // Attributes set internally by init():
    var self = {
        start: null
    };

    // Methods //

    self.init = function (options) {
        var property, givenValue, defaultValue;
        options = options || {};
        for (property in defaults) {
            givenValue = options[property];
            defaultValue = defaults[property];
            if (givenValue === undefined) {
                if (defaultValue === Required) {
                    throw 'init: "' + property + '" required';
                }
                self[property] = defaultValue;
            } else {
                self[property] = givenValue;
            }
        }

        if (self.dataURL === null) {
            self.dataURL = edgeflip.router.reverse('gimmick:engage-data', self.taskId);
        }

        $(function () {
            self.start = new Date();
            self.poll();
        });
    };

    var pollSuccess = function (data) {
        var elapsed, remaining;
        switch (data.status) {
            case 'waiting':
                setTimeout(self.poll, 500);
                break;
            case 'success':
                self.results = data.results;
                elapsed = new Date() - self.start,
                remaining = elapsed < 1500 ? 1500 - elapsed : 0;
                //self.totalScore = totalScore(self.scores);
                //self.scores.unshift(self.header);
                setTimeout(self.displayScores, remaining);
                break;
            default:
                throw "Bad status: " + data.status;
        }
    };

    var pollError = function () {
        alert("No results"); // FIXME?
    };

    self.poll = function () {
        /* Poll the JSON data endpoint.
         *
         * On success, store the data and display the scores via displayScores().
         */
        $.ajax({
            type: 'GET',
            url: self.dataURL,
            dataType: 'json',
            error: pollError,
            success: pollSuccess
        });
    };

    self.displayScores = function () {
        var on = $('.switch.on'),
            off = $('.switch').not(on);

        on.fadeOut(function () {
            off.fadeIn(function () {
                // Clean up initialization classes
                on.add(off).toggleClass('on').toggleClass('in');
            });
        });

        $('#city_rank').text(self.results.city.rank);
        $('#user_city').text(self.results.city.user_city);
        $('#user_state').text(self.results.city.user_state);
        $('#age_rank').text(self.results.age.rank);
        $('#user_age').text(self.results.age.user_age);
        $('#friend_rank').text(self.results.friends.rank);
        var friends = self.results.friends.top;
        for (var i in friends) {
            var friend = friends[i];
            $('#friend_list ol').append('<li>' + friend.first_name + ' ' + friend.last_name + '</li>');
        }
        var likes = self.results.greenest_likes;
        if (likes.length == 0) {
            $('#like_list ul').append('No green likes, sad face');
        }
        for (var i in likes) {
            var like = likes[i];
            // available: like.name, like.page_id
            $('#like_list ul').append('<li>' + like.name + '</li>');
        }
        var posts = self.results.greenest_posts;
        if (posts.length == 0) {
            $('#post_list ul').append('No green posts, sad face');
        }
        for (var i in posts) {
            var post = posts[i];
            // available: post.message, post.post_id, post.score
            $('#post_list ul').append('<li>' + post.message + ' Green Score of ' + post.score + '</li>');
        }
    };

    return self;
})(edgeflip, jQuery);
