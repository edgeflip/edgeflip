$(document).ready(init);

function init() {
    // first pageview, get summary data and draw main table
    mksummary();

    // set default sorting metric, bind click handler
    window.metric = 'visits';
    $('#sumtable th').click(sort);

    // though we bind the sort handler to the entire th, style the actual buttons
    $('.sorter').button({
        'icons': {
            'secondary': 'ui-icon-arrow-2-n-s'
        },
        'text': true
    });
}


function mksummary() {
    // initial load of summary data, the first view
    
    // if the clientpicker is on, disable it while we're loading data to stop async races
    $('#clientpicker').attr('disabled', 'disabled');

    // send a client_id if we're a superuser, else send 0 and the server will check auths 
    var client_id = $('#clientpicker').length == 1 ? $('#clientpicker option:selected').val() : 0;

    $.get("/reporting/client/" + client_id + "/summary/", function(response) {
        // turn off our loading gif
        $('.loading').hide();

        // clear old data if this is a superuser change
        $('tbody').remove();
        $('#clientpicker').removeAttr('disabled');

        window.response = response; 

        // we're manually adding column headers in the template right now, TODO, send this serverside
        var columns = ['name', 'visits', 'clicks', 'uniq_auths', 'shown', 'shares', 'audience', 'clickbacks'];
        var table = d3.select('#sumtable');

        // build rows
        var body = table.append("tbody");
        var rows = body.selectAll("tr").data(window.response)
            .enter()
            .append("tr")
            .attr("class", "child")
            .attr("id", function(d) {
                return d.root_id;
            });

        // build cells per row
        rows.selectAll("td").data(
            /* so for each row, we end up wanting an array of values, in column order */
            function(row) {
                // columns.map makes a nice [] of datapoints per row
                return columns.map(function(column) {
                    return row[column];
                });
            })
            .enter()
            .append("td")
            .text(function(d) {
                return d;
            })
            .attr("class", "datapoint");

        // and a chart-toggler at the end
        rows.append("td")
            .append("button")
            .attr("class", "charter")
            .attr("root-id", function(d) {
                return d.root_id;
            });

        // make them jquery buttons
        $('.charter').button({
            'icons': {
                'primary': 'ui-icon-image'
            },
            'text': false
        });
        // bind a click function for charts
        $('button.charter').click(mkchart);

        // and a final summary row
        body.append("tr").attr("class", "totals")
            .selectAll("td")
            .data(columns)
            .enter()
            .append("td")
            .text(function(metric, i) {
                return i === 0 ? 'TOTALS' : d3.sum(window.response.map(function(d) {
                    return d[metric];
                }));
            })
            .attr("class", "datapoint");

    });
}


function sort() {
    /* take a click on a table header and sort the summary rows */

    var metric = this.id;
    if (metric == window.metric) {
        // toggling sort order if they've clicked the same metric
        window.sorter = window.sorter === d3.ascending ? d3.descending : d3.ascending;
    } else {
        // else a new metric, set to descending by default
        window.sorter = d3.descending;
    }

    var sortstyle = window.sorter === d3.descending ? 'descend' : 'ascend';

    // clear old styles
    $('th').removeClass('ascend descend');

    // reset button styles
    $('.sorter').button({
        'icons': {
            'secondary': 'ui-icon-arrow-2-n-s'
        },
        'text': true
    });

    // set new styles
    $('.tableFloatingHeaderOriginal #' + metric).addClass(sortstyle);
    $('.tableFloatingHeader #' + metric).addClass(sortstyle);
    $(this).addClass(sortstyle);

    // set new button icon (up or down), on floating header _and_ original
    var toggle = sortstyle == 'descend' ? 'ui-icon-arrowthick-1-s' : 'ui-icon-arrowthick-1-n';
    $('.tableFloatingHeaderOriginal #' + metric + ' .sorter').button('option', 'icons', {
        secondary: toggle
    });
    $('.tableFloatingHeader #' + metric + ' .sorter').button('option', 'icons', {
        secondary: toggle
    });

    window.metric = metric;

    // and.. actually sort the data
    d3.selectAll("tr.child").sort(function(a, b) {
        return window.sorter(a[metric], b[metric]);
    });
}


// CAMPAIGN DETAILS SPAWNED FROM BUTTON PER ROW 

function mkchart() {
    /* on click of a campaign chart button, fetch hourly data points and draw some charts */

    var client_id = $('#clientpicker').length == 1 ? $('#clientpicker option:selected').val() : 0;
    var campaign_id = $(this).attr('root-id');
    $.get('/reporting/client/' + client_id + '/campaign/' + campaign_id + '/hourly', on_hourly);

    // stash this so other UI elements know which campaign is selected
    window.campaign_id = campaign_id;

    // open a blank modal so the user knows the button click registered
    $('#modal').dialog({
        'modal': true,
        'width': 1000
    }); // pass height if you need to
    $('#modal').on("dialogclose", function() {
        /* TODO: this could be more graceful with more clever naming, probably       
         * but on a closing of the modal popup, wipe out old things and reset the
         * state of the modal to blank/loading
         */

        // clear old data if it exists (viewing one chart, then another)
        $('.chart').children().remove();
        $('#hourlytable tbody').children().remove();
        $('#legend').children().remove();
        $('#slider').children('a').remove();
        $('#xAxis').children().remove();
        $('#yAxis').children().remove();
        $('#hourlygraph').children().remove();

        // reset the modal to show the loading spinner
        $('#hourlytable').hide();
        $('#chart_container').hide();
        $('#tsver').hide();
        $('#modal .loading').show();
    });
}


function on_hourly(response) {
    // receipt of hourly data for this campaign, draw some charts
    window.response = response;

    // turn off loading spinner, show the TSV data button
    $('#modal .loading').hide();
    $('#tsver').show();

    // stash this data on window, axes and controls use this also
    window.daterange = window.response.data.map(function(row) {
        return new Date(row.time);
    });

    // construct the graphical bits
    mkgraph('#graph', response);

    // then reveal the parent container
    $('#chart_container').show();


    // the control for revealing TSV data
    $('#tsver').button();
    $('#tsver').off('click').on('click', tsv_data);
}


function mkgraph(element, response) {

    var palette = new Rickshaw.Color.Palette();

    var graph = new Rickshaw.Graph({
        element: document.querySelector(element),
        width: 600,
        height: 300,
        renderer: 'line',

        // Rickshaw wants one array per type of data, so generate each one with a map() on 
        // the data we've sent from the server.. there is probably a clever way to inspect
        // the response and do this automagically in one line of code
        series: [{
            name: "Visits",
            data: response.data.map(function(row) {
                return {
                    x: new Date(row.time).getTime() / 1000,
                    y: row.visits
                };
            }),
            color: palette.color(),
        }, {
            name: "Clicks",
            data: response.data.map(function(row) {
                return {
                    x: new Date(row.time).getTime() / 1000,
                    y: row.clicks
                };
            }),
            color: palette.color(),
        }, {
            name: "Unique Auths",
            data: response.data.map(function(row) {
                return {
                    x: new Date(row.time).getTime() / 1000,
                    y: row.uniq_auths
                };
            }),
            color: palette.color(),
        }, {
            name: "Faces Shown",
            data: response.data.map(function(row) {
                return {
                    x: new Date(row.time).getTime() / 1000,
                    y: row.shown
                };
            }),
            color: palette.color(),
        }, {
            name: "Shares",
            data: response.data.map(function(row) {
                return {
                    x: new Date(row.time).getTime() / 1000,
                    y: row.shares
                };
            }),
            color: palette.color(),
        }, {
            name: "Audience",
            data: response.data.map(function(row) {
                return {
                    x: new Date(row.time).getTime() / 1000,
                    y: row.audience
                };
            }),
            color: palette.color(),
        }, {
            name: "Clickbacks",
            data: response.data.map(function(row) {
                return {
                    x: new Date(row.time).getTime() / 1000,
                    y: row.clickbacks
                };
            }),
            color: palette.color(),
        }, ]
    });

    // turn on the various Rickshaw features

    // Hover details
    new Rickshaw.Graph.HoverDetail({
        graph: graph,
        yFormatter: function(x) {
            return x;
        }
    });

    // Legend
    var legend = new Rickshaw.Graph.Legend({
        graph: graph,
        element: document.getElementById('legend')
    });

    // Legend controls
    var highlight = new Rickshaw.Graph.Behavior.Series.Highlight({
        graph: graph,
        legend: legend
    });

    // Legend controls
    var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
        graph: graph,
        legend: legend
    });

    // The slider control for selecting start/end times
    var slider = new Rickshaw.Graph.RangeSlider({
        graph: graph,
        element: document.getElementById('slider')
    });

    graph.render();

    // AXES
    var xAxis = new Rickshaw.Graph.Axis.X({
        graph: graph,
        ticks: 4,
        orientation: 'bottom',
        element: document.getElementById('xAxis'),
        tickFormat: function(x) {
            // find range to display either dates or times .. ideally calc this not for every tick (once per update)
            var stacktimes = graph.series[0].stack.map(function(row) {
                return row.x;
            });
            var tdelta = d3.max(stacktimes) - d3.min(stacktimes);

            var d = new Date(x * 1000);
            return tdelta > 86400 ? d.toLocaleDateString() : d.toLocaleTimeString();
        }
    });
    xAxis.render();

    var yAxis = new Rickshaw.Graph.Axis.Y({
        graph: graph,
        orientation: 'left',
        ticks: 4,
        element: document.getElementById('yAxis'),
    });
    yAxis.render();

    // permanent X min and maxes
    var extents = d3.extent(response.data, function(row) { return new Date(row.time);
    });
    $('#xMin').text(extents[0].toLocaleDateString());
    $('#xMax').text(extents[1].toLocaleDateString());
}



function tsv_data(response) {

    /* Load the data and build up the table element, then toggle displays */

    // we're manually adding column headers in the template right now, TODO, send this serverside
    var columns = ['time', 'visits', 'clicks', 'uniq_auths', 'shown', 'shares', 'audience', 'clickbacks'];
    var table = d3.select('#hourlytable');

    // build rows
    var body = table.append("tbody");
    var rows = body.selectAll("tr").data(window.response.data)
        .enter()
        .append("tr");

    // build cells per row
    rows.selectAll("td").data(
        /* so for each row, we end up wanting an array of values, in column order */
        function(row) {
            // columns.map makes a nice [] of datapoints per row
            return columns.map(function(column) {
                return row[column];
            });
        })
        .enter()
        .append("td")
        .text(function(d) {
            return d + '\t';
        })
        .attr("class", "datapoint");

    // toggle visibility .. kinda awkward
    $('#chart_container').hide();
    $('#hourlytable').show();

    // toggle button functionality
    $('#tsver span').text('Data as Graphs');
    $('#tsver').off('click').on('click', function() {
        $('#hourlytable').hide();
        $('#chart_container').show();
        $('#tsver span').text('Data as TSV');
        $('#tsver').off('click').on('click', tsv_data);
    });
}
