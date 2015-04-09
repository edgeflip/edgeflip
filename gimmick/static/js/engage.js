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
                setTimeout(self.displayResults, remaining);
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
         * On success, store the data and display the scores via displayResults().
         */
        $.ajax({
            type: 'GET',
            url: self.dataURL,
            dataType: 'json',
            error: pollError,
            success: pollSuccess
        });
    };

    self.displayResults = function () {
        var on = $('.switch.on'),
            off = $('.switch').not(on);

        on.fadeOut(function () {
            off.fadeIn(function () {
                // Clean up initialization classes
                on.add(off).toggleClass('on').toggleClass('in');
            });
        });

        $('#city-rank').text(self.results.city.rank);
        $('#user-city').text(self.results.city.user_city);
        $('#user-state').text(self.results.city.user_state);
        $('#age-rank').text(self.results.age.rank);
        $('#user-age').text(self.results.age.user_age);
        $('#friend-rank').text(self.results.friends.rank);

        self.results.friends.top.forEach(function (friend) {
            var name = friend.first_name + ' ' + friend.last_name,
                img = $('<img>', {
                    'class': 'profile-picture',
                    'src': 'https://graph.facebook.com/' + friend.fbid + '/picture'
                });

            $('<li></li>').append(img, name).appendTo($('#friend-list'));
        });

        if (self.results.greenest_likes.length === 0) {
            $('#like-list').append('No green likes.');
        } else {
            self.results.greenest_likes.forEach(function (page) {
                $('#like-list').append('<a href="https://facebook.com/' + page.page_id + '"><img src="https://graph.facebook.com/' + page.page_id + '/picture?height=75" class="green-like" /></a>');
            });
        }

        if (self.results.greenest_posts.length == 0) {
            $('#post-list-container').append('No green posts.');
            $('#post-list').hide();
        } else {
            self.results.greenest_posts.forEach(function (post) {
                var img = post.picture ? '<img src="' + post.picture + '">' : '';
                // Available: post.message, post.post_id, post.score
                $('#post-list').append('<tr><td class=post-img>' + img + '</td><td><a href="https://facebook.com/' + post.post_id + '">' + post.message + '</a></td><td class=post-score>' + Math.round(post.score*100) + '</td></tr>');
            });
        }
    };

    return self;
})(edgeflip, jQuery);
