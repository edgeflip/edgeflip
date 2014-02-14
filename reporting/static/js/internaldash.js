$(document).ready(init)

function init() {
    // first pageview, get summary data and draw main table
    var csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
    $.post('/reporting/edgedash/', {'csrfmiddlewaretoken': csrfToken}, function(response) {

        window.response = response;

        var height = 300;
        var width = 800;

        var chart = d3.select('#graph').append('svg')
            .attr('width', width)
            .attr('height', height)

        // var tdata = response.data.map( function(row){return new Date(row.hour)})
        var x = d3.scale.linear()
            .domain( d3.extent(response.data, function(row) {return new Date(row.hour)}) )
            .range([0,width])

        var y = d3.scale.log()
            .domain( d3.extent(response.data, function(row) {console.log(row); return row.count}) )
            .range([0,height])

        var keys = d3.set( response.data.map( function(row) {return row.type}) ).values().sort(d3.ascending);
        var z = d3.scale.linear().range(['#F00', '#00F']).domain([0,keys.length])

        chart.selectAll("rect").data(response.data)
            .enter().append("rect")
            .attr('x', function(d) {return x(new Date(d.hour)) + keys.indexOf(d.type)})
            .attr('y', function(d) {return height- (y(d.count))}) // actually.. shouldn't this be a flat line?
            .attr('width', 2)
            .attr('height', function(d,i) {return y(d.count)})
            .attr('fill', function(d,i) {return z(keys.indexOf(d.type))})

        var line = d3.svg.line()
            .x(function(d) { return x(new Date(d.hour)); })
            .y(function(d) { return height - y(d.count) })
            .interpolate("basis");

        chart.selectAll("path").data(response.data)
            .enter().append('path')
            .attr('d', line)


        })
    }

