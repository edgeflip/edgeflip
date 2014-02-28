{% comment %}
JavaScript include template for the heartbeat event record

Requires:
    edgeflip.Event

Use:
    var heartbeat = new edgeflip.Heartbeat();
    heartbeat.stop();
    heartbeat.start();
    heartbeat.reset();

{% endcomment %}
edgeflip.Heartbeat = function (options) {
    options = options || {};
    this.maxCount = options.maxCount || 60;
    this.timeout = options.timeout || 2000;
    this.reset();
    this.start();
};
edgeflip.Heartbeat.prototype.run = function () {
    if (this.on && this.count < this.maxCount) {
        edgeflip.Event.record('heartbeat');
        this.count += 1;

        var bound = this.run.bind(this); // setTimeout runs in global scope
        setTimeout(bound, this.timeout);
    }
};
edgeflip.Heartbeat.prototype.start = function () {
    this.on = true;
    this.run();
};
edgeflip.Heartbeat.prototype.stop = function () {
    this.on = false;
};
edgeflip.Heartbeat.prototype.reset = function () {
    this.count = 0;
};
