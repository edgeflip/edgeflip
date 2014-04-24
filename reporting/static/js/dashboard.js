edgeflip.dashboard = (function (edgeflip, $) {
    var self = {
        client_id: null,
        metrics: {
            'visits': 'Visits',
            'authorized_visits': 'Authorized Visits',
            'uniq_users_authorized': 'Users Authorized',
            'auth_fails': 'Authorization Fails',
            'visits_generated_faces': 'Visits Generated Faces',
            'visits_shown_faces': 'Visits Shown Faces',
            'visits_with_shares': 'Visits With Shares',
            'total_shares': 'Total Shares',
            'clickbacks': 'Clickbacks',
        }
    };

    self.columns = $.extend({'name': 'Campaign'}, self.metrics)

    self.init = function() {
        self.set_client_id()
        // first pageview, get summary data and draw main table

        // set default sorting metric, bind click handler
        window.metric = 'visits';
        $('#sumtable th').click(self.sort);

        // though we bind the sort handler to the entire th, style the actual buttons
        $('.sorter').button({
            'icons': {
                'secondary': 'ui-icon-arrow-2-n-s'
            },
            'text': true
        });
    }


    self.set_client_id = function() {
        self.client_id = $('#clientpicker').val();
        self.mksummary();
    }

    self.on_fail = function(response) {
        console.log('fail');
        $('.loading').hide();
        alert('Error message: ' + response.responseText);
    }


    self.on_summary = function(response) {
        // turn off our loading gif
        $('.loading').hide();

        // clear old data if this is a superuser change
        $('tbody').remove();
        $('#clientpicker').removeAttr('disabled');

        window.response = response;

        var table = d3.select('#sumtable');

        // build rows
        var body = table.append("tbody");
        var rows = body.selectAll("tr").data(window.response.data)
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
                return Object.keys(self.columns).map(function(col) {
                    return row[col];
                });
            })
            .enter()
            .append("td")
            .text(function(d) {
                return d;
            })
            .attr("class", "datapoint");

        // a chart-toggler at the end
        rows.append("td")
            .append("button")
            .attr("class", "record icon charter")
            .attr("root-id", function(d) {
                return d.root_id;
            });

        $('.charter').button({
            'icons': {
                'primary': 'ui-icon-image'
            },
            'text': false
        });
        $('button.charter').click(self.mkchart);

        // a tsv report downloader
        rows.append("td")
            .append("button")
            .attr("class", "record icon report")
            .attr("root-id", function(d) {
                return d.root_id;
            });

        $('.report').button({
            'icons': {
                'primary': 'ui-icon-document'
            },
            'text': false
        });
        $('button.report').click(function() {
            var campaign_id = $(this).attr('root-id')
            base_url = edgeflip.router.reverse('reporting:campaign_hourly', self.client_id, campaign_id);
            window.location = base_url + "?format=csv"
        });

        // and a final summary row
        var totals = body.append("tr")
            .attr("class", "totals")

        totals.append("td").text("TOTALS")
        totals.selectAll("tr")
            .data(Object.keys(self.metrics))
            .enter()
            .append("td")
            .text(function(d) {
                return window.response.rollups[0][d];
            })
            .attr("class", "datapoint");
    }

    self.mksummary = function() {
        // if the clientpicker is on, disable it while we're loading data to stop async races
        $('#clientpicker').attr('disabled', 'disabled');

        // send a client_id if we're a superuser, else send 0 and the server will check auths 
        $.get(edgeflip.router.reverse('reporting:client_summary', self.client_id), self.on_summary).fail(self.on_fail);
    }


    self.sort = function() {
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

    self.mkchart = function() {
        /* on click of a campaign chart button, fetch hourly data points and draw some charts */

        var campaign_id = $(this).attr('root-id');
        $.get(edgeflip.router.reverse('reporting:campaign_hourly', self.client_id, campaign_id), self.on_hourly);

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
            $('#legend').children().remove();

            // reset the modal to show the loading spinner
            $('#chart_container').hide();
            $('#modal .loading').show();
        });
    }


    self.on_hourly = function(response) {
        // receipt of hourly data for this campaign, draw some charts
        window.response = response;

        // turn off loading spinner
        $('#modal .loading').hide();

        // stash this data on window, axes and controls use this also
        window.daterange = window.response.data.map(function(row) {
            return new Date(row.time);
        });

        // construct the graphical bits
        self.mkgraph('#graph', response);

        // then reveal the parent container
        $('#chart_container').show();

    }


    self.mkgraph = function(element, response) {

        var palette = new Rickshaw.Color.Palette();

        var graph = new Rickshaw.Graph({
            element: document.querySelector(element),
            width: 600,
            height: 300,
            renderer: 'line',

            series: Object.keys(self.metrics).map(function(col) {
                return {
                    name: self.metrics[col],
                    data: response.data.map(function(row) {
                        return {
                            x: new Date(row.time).getTime() / 1000,
                            y: row[col]
                        };
                    }),
                    color: palette.color(),
                };
            }),
        });
        graph.render();

        // turn on the various Rickshaw features

        // The slider control for selecting start/end times
        var slider = new Rickshaw.Graph.RangeSlider({
            graph: graph,
            element: document.getElementById('slider')
        });

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


        // AXES
        var xAxis = new Rickshaw.Graph.Axis.X({
            graph: graph,
            ticks: 4,
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
            ticks: 4,
        });
        yAxis.render();

        // permanent X min and maxes
        var extents = d3.extent(response.data, function(row) { return new Date(row.time);
        });
        //$('#legend_header').text(
        $('#xMin').text(extents[0].toLocaleDateString());
        $('#xMax').text(extents[1].toLocaleDateString());
    }

    return self;
})(edgeflip, jQuery);
