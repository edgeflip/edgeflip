google.load("visualization", "1.0", {"packages": ["table", "corechart"]});
// google.load('jquery', '1.4.2');
google.setOnLoadCallback(init);

function init() {
    // first pageview, get data for newest campaign and draw a chart
    getData();
    }

function getData(campaign, date) {
    // no need to post client, the server can pick that out of whatever user
    $.post('/dashboard/chartdata/', {'campaign':'aggregate', 'day':'today'}, on_data);
    }

function on_data(response) {

    // create and maintain, 2 "DataTables" to store data at hourly and daily resolutions
    window.dailydata = new google.visualization.DataTable({'cols':response.cols, 'rows':response.daily});
    window.monthlydata = new google.visualization.DataTable({'cols':response.cols, 'rows':response.monthly});

    render();

    }



function render() {

    var hourly_agg_div = document.createElement("div");
    hourly_agg_div.id = "hourly_agg_div";
    var hr_agg_options = {title: 'Hourly Report', enableInteractivity: 'true', 'width': 1000};
    var hr_agg_chart = new google.visualization.LineChart(hourly_agg_div);
    hr_agg_chart.draw(window.dailydata, hr_agg_options);


    var daily_agg_div = document.createElement("div");
    daily_agg_div.id = "daily_agg_div";
    var daily_chart = new google.visualization.LineChart(daily_agg_div);
    daily_chart.draw(window.monthlydata, {title: 'Daily Report(for the last 30 days)', enableInteractivity: 'true', 'width': 1000});


    // Add the div to the document that contains our Aggregate_Table

    document.body.appendChild(hourly_agg_div);
    document.body.appendChild(daily_agg_div);
}


function mkCampaigns() {

    // campaign chooser


    /* 
    // create the first second that lists out our campaigns for this client
    var client = document.createElement('p');
    client.innerHTML = 'Campaigns Currently Running for <b>{{client_name}}</b>';
    var items = document.createElement('ul');
    for (i=0; i < all_keys.length; i++)
    {
        var cur = document.createElement('li');
        var cur_link = document.createElement('a');
        var cur_link_href = "#aggregate_campaign_{0}";
        cur_link_href = cur_link_href.replace('{0}', i.toString());
        cur_link.href = cur_link_href;
        cur_link.innerHTML = all_keys[i];
        cur.appendChild(cur_link);
        items.appendChild(cur);
    }
    document.body.appendChild(client);
    document.body.appendChild(items);
    document.body.appendChild(document.createElement('br'));
    document.body.appendChild(document.createElement('br'));
    document.body.appendChild(document.createElement('hr'));
    */
    // end campaign chooser widget
    //
    }
