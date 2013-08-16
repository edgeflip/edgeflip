google.load("visualization", "1.0", {"packages": ["table", "corechart"]});
// google.load('jquery', '1.4.2');
google.setOnLoadCallback(init);

function init() {
    // first pageview, get data for newest campaign and draw a chart
    getData();
    window.dailychart = new google.visualization.LineChart( $('#daily')[0] );
    window.monthlychart = new google.visualization.LineChart( $('#monthly')[0] );
    }


function getData(campaign, date) {
    // no need to post client, the server can pick that out of whatever user
    $.post('/dashboard/chartdata/', {'campaign':'aggregate', 'day':'today'}, on_data);
    }


function on_data(response) {
    // update data tables
    window.dailydata = new google.visualization.DataTable({'cols':response.cols, 'rows':response.daily});
    window.monthlydata = new google.visualization.DataTable({'cols':response.cols, 'rows':response.monthly});

    // redraw charts
    var hr_agg_options = {title: 'Hourly Report', enableInteractivity: 'true', 'width': 1000};
    window.dailychart.draw(window.dailydata, hr_agg_options);
    window.monthlychart.draw(window.monthlydata, {title: 'Daily Report(for the last 30 days)', enableInteractivity: 'true', 'width': 1000});
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
    }
