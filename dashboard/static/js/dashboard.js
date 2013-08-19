google.load("visualization", "1.0", {"packages": ["table", "corechart"]});
// google.load('jquery', '1.4.2');
google.setOnLoadCallback(init);

function init() {
    // first pageview, get data for newest campaign and draw a chart
    getData();
    window.dailychart = new google.visualization.LineChart( $('#daily')[0] );
    window.monthlychart = new google.visualization.LineChart( $('#monthly')[0] );

    // load up datepicker widgets
    $( "#datepicker" ).datepicker({gotoCurrent:true, onSelect:getData});
    }


function getData() {
    // no need to post client, the server can pick that out of whatever user
    day = $.datepicker.formatDate('mm/dd/yy', $('#datepicker').datepicker('getDate'));
    campaign = 'aggregate';
    $.post('/dashboard/chartdata/', {'campaign':campaign, 'day':day}, onData);
    }


function onData(response) {
    // update data tables
    window.dailydata = new google.visualization.DataTable({'cols':response.cols, 'rows':response.daily});
    window.monthlydata = new google.visualization.DataTable({'cols':response.cols, 'rows':response.monthly});

    // redraw charts
    var dailyopts = {
        title: 'Hourly Volume', 
        enableInteractivity: 'true', 
        width: 580, 
        height:160,
        chartArea: {width:500},
        lineWidth: 1, // set this a bit thinner than monthly 

        // curveType: 'function', // nice curves but it messes up vaxis calcs
        legend: {position: 'none'}, // kill this legend, we'll hack into the bigger one below
        // "turn off" the gridlines, but keep unit labels on axes
        vAxis: {gridlines: {color:'#FFF'}},
        hAxis: {gridlines: {color:'#FFF', count:12}},

        // backgroundColor: {strokeWidth: 1, stroke: 'red'},
        };

    window.dailychart.draw(window.dailydata, dailyopts);

    window.monthlychart.draw(window.monthlydata, {
        title: 'Daily Volume', 
        enableInteractivity: 'true', 
        chartArea:{left:50,},
        width: 799,
        height:250,
        legend: {position: 'right', textStyle: {fontSize:10}, alignment: 'end'},

        // "turn off" the gridlines, but keep unit labels on axes
        vAxis: {gridlines: {color:'#FFF'}},
        hAxis: {gridlines: {color:'#FFF'}},
        // backgroundColor: {strokeWidth: 1, stroke: 'red'},
        });
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
