window.onload = init

function init() {
    // first pageview, get data for newest campaign and draw a chart
    getData();

    // load up datepicker widgets
    $( "#datepicker" ).datepicker({gotoCurrent:true, onSelect:getData});

    }


function getData() {
    // no need to post client, the server can pick that out of whatever user
    day = $.datepicker.formatDate('mm/dd/yy', $('#datepicker').datepicker('getDate'));
    campaign = $('#campaignpicker select').val();
    $.post('/dashboard/chartdata/', {'campaign':campaign, 'day':day}, onData);
    }


function onData(response) {

    // reset valid dates in the jquery widget
    window.response = response;
    $('#datepicker').datepicker( "option", "minDate", response.minday);
    $('#datepicker').datepicker( "option", "maxDate", response.maxday);

    window.data = JSON.parse(response.daily);
    draw();

    }


function draw() {

    var barwidth = 6;

    // wipe previous sets
    $('#daily').children().remove();

    // set axis scales
    var hscale = d3.scale.linear().domain([0, 23]).range([40, 560-barwidth]);
    var vscale = d3.scale.linear().domain([0,d3.max( d3.max(data))]).range([1, 180]);
    var colorscale = d3.scale.linear().domain([0,8]).interpolate(d3.interpolateRgb).range(["#ff0000", "#0000ff"]);

    // draw a box per hour per row
    for (row in data) {
        rowdata = data[row]
        d3.select('#daily').selectAll(".r"+row).data(rowdata).enter().append("rect").
            attr("x", function(datum, index) { return row<4? hscale(index)-4 : hscale(index)+4;}).
            attr("x", function(datum, index) { return row<4? hscale(index)-4 : hscale(index)+4;}).
            attr("y", function(datum) { return 180 - vscale(datum);}).
            attr("height", function(datum) { return vscale(datum);}).
            attr("width", barwidth).
            attr("fill", function(d,i){return colorscale(row)}).
            attr("class", "r"+row);
        }

    // label X axis
    d3.select('#daily').selectAll("text.hourlabel").
        data(hscale.ticks()).
        enter().append("text").
        attr("x", function(datum, index) { return hscale(datum); }).
        attr("y", 200).
        attr("dx", barwidth/2). // so this centers horizontally.. but why not just bake it into the x coord?
        attr("text-anchor", "middle").
        attr("style", "font-size: 10; font-family: Helvetica, sans-serif").
        text(function(datum) {if (datum%12==0) datum += 12; return datum<=12 ? datum+'A':((datum-12)+'P'); }).
        attr("class", "hourlabel");

    // label Y axis
    $('.datalabel').remove();
    d3.select('#daily').selectAll("text.datalabel").  // worst name evar
        data( vscale.ticks() ).
        enter().append("text").
        attr("x", 15).
        attr("y", function(datum, index) { return 180-vscale(index)}).
        // should probably just throw all this text stuff into a CSS file
        attr("text-anchor", "middle").
        attr("style", "font-size: 10; font-family: Helvetica, sans-serif").
        text(function(datum, index) { return datum; }).
        attr("class", "datalabel");


    mkLegend(barwidth);
    }


function mkLegend(barwidth) {
    // clear whatever's there
    jlegend = $('#legend');
    jlegend.children().remove()

    var height = jlegend.height()
    var width = jlegend.width()

    // set axes scale... probably only need one, reuse the color ?
    var vscale = d3.scale.linear().domain([0, response.metrics.length/2]).range([1, height]);
    var colorscale = d3.scale.linear().domain([0, response.metrics.length]).interpolate(d3.interpolateRgb).range(["#ff0000", "#0000ff"]);
    
    for (metric in response.metrics) {
        d3.select("#legend").selectAll("text").
        data(response.metrics).
        enter().
        // text labels
        append("text").
        attr("x", function(d,i) { return i<4 ? 15 : 250}).
        attr("y", function(d,i) { return height-vscale(i%5)}). 
        text( function(datum) { return datum.label;}).
        attr("fill", function(d,i) { return colorscale(i)})  // hrm, .attr OR .style works here

        // what's a legend without boxes
        d3.select("#legend").selectAll("rect").
        data(response.metrics).enter().
        append("rect").
        attr("x", function(d,i) { return i<4 ? 5 : 240}).
        attr("y", function(d,i) { return (height-vscale(i%5))-barwidth}).
        attr("height", barwidth).
        attr("width", barwidth).
        attr("fill", function(d,i){return colorscale(i)})
        }

    }


