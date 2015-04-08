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
                self.scores = data.scores;
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

        console.log(self.scores) // TODO
    };

    return self;
})(edgeflip, jQuery);
