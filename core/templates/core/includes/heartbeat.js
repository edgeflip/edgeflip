{% comment %}
JavaScript include template for the heartbeat event record

Requires:
    recordEvent

Use:
    var heartbeat = new Heartbeat();
    heartbeat.stop();
    heartbeat.start();
    heartbeat.reset();

{% endcomment %}
var Heartbeat = function (options) {
    options = options || {};
    this.maxCount = options.maxCount || 60;
    this.timeout = options.timeout || 2000;
    this.reset();
    this.start();
};
Heartbeat.prototype.run = function () {
    if (this.on && this.count < this.maxCount) {
        recordEvent('heartbeat');
        this.count += 1;

        var bound = this.run.bind(this); // setTimeout runs in global scope
        setTimeout(bound, this.timeout);
    }
};
Heartbeat.prototype.start = function () {
    this.on = true;
    this.run();
};
Heartbeat.prototype.stop = function () {
    this.on = false;
};
Heartbeat.prototype.reset = function () {
    this.count = 0;
};
