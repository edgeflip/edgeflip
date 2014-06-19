define( [ 'targetshare/js/events' ], function( events ) {
    var heartbeat = function (options) {
        options = options || {};
        this.maxCount = options.maxCount || 450;
        this.timeout = options.timeout || 2000;
        this.reset();
        this.start();
    };
    heartbeat.prototype.run = function () {
        if (this.on && this.count < this.maxCount) {
            events.record('heartbeat');
            this.count += 1;

            var bound = this.run.bind(this); // setTimeout runs in global scope
            setTimeout(bound, this.timeout);
        }
    };
    heartbeat.prototype.start = function () {
        this.on = true;
        this.run();
    };
    heartbeat.prototype.stop = function () {
        this.on = false;
    };
    heartbeat.prototype.reset = function () {
        this.count = 0;
    };

    return heartbeat;
} );
