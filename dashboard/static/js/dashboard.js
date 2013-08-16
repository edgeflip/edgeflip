google.load("visualization", "1.0", {"packages": ["table", "corechart"]});
// google.load('jquery', '1.4.2');
google.setOnLoadCallback(init);

function init() {

    // first pageview, get data for newest campaign and draw a chart
    data = getData();
    drawStuff();

    // we want to have at any time, 2 "DataTables" to store data at hourly and daily resolutions

    }



function getData(campaign, date) {

    // no need to post client, the server can pick that out of whatever user
    $.post('/dashboard/chartdata/', {'campaign':'aggregate', 'day':'today'});

    }


function drawStuff()
{

    // AGGREGATE CAMPAIGN DISPLAY WITH ALL CAMPAIGNS INCLUDED
    // create the div to put it in
    var agg_div = document.createElement("div");
    agg_div.id = "agg_div";

    var Data = new google.visualization.DataTable();
    Data.addColumn('number', 'Visits');
    Data.addColumn('number', 'Clicks');
    Data.addColumn('number', 'Authorizations');
    Data.addColumn('number', 'Unique Authorized Facebook Users');
    Data.addColumn('number', 'Users Shown Friends');
    Data.addColumn('number', 'Users Who Shared');
    Data.addColumn('number', 'Friends Shared With');
    Data.addColumn('number', 'Unique Friends Shared');
    Data.addColumn('number', 'Clickbacks');
    Data.addRows([aggregate_json.data]);

    var Aggregate_Table = new google.visualization.Table(agg_div);
    Aggregate_Table.draw(Data, {showRowNumberPosition: 'true', width:'100%', position: 'out'});


    // TODAY CAMPAIGN DISPLAY WITH ALL CAMPAIGNS INCLUDED
    var today_div = document.createElement("div");
    today_div.id = "today_div";

    var Data1 = new google.visualization.DataTable();
    Data1.addColumn('number', 'Visits');
    Data1.addColumn('number', 'Clicks');
    Data1.addColumn('number', 'Authorizations');
    Data1.addColumn('number', 'Distinct Authorized Facebook Users');
    Data1.addColumn('number', '# Users Shown Friends');
    Data1.addColumn('number', '# Users Who Shared');
    Data1.addColumn('number', '# Friends Shared With');
    Data1.addColumn('number', '# Distint Friends Shared');
    Data1.addColumn('number', 'Clickbacks');
    Data1.addRows([today_json.data]);

    var Today_Table = new google.visualization.Table(today_div);
    Today_Table.draw(Data1, {showRowNumberPosition: 'true', width: '100%', position: 'out'});



    // LINE CHART FOR HOULY DATA FOR ALL CAMPAIGNS
    var hourly_agg_div = document.createElement("div");
    hourly_agg_div.id = "hourly_agg_div";
    var hourly_agg_arr = new Array();
    hourly_agg_arr[0] = ['Hour', 'Visits', 'Clicks', 'Authorizations', 'Distinct Authorized Facebook Users', '# Users Shown Friends', '# Users Who Shared', '# Friends Shared With', '# Distinct Friends Shared', 'Clickbacks'];
    for(w=0; w < hourly_aggregate.data.length; w++)
    {
        hourly_agg_arr[w+1] = hourly_aggregate.data[w];
    }
    var hr_agg_data = google.visualization.arrayToDataTable(hourly_agg_arr);
    var hr_agg_options = {title: 'Hourly Report', fontSize: '10', enableInteractivity: 'true', 'width': 1000};
    var hr_agg_chart = new google.visualization.LineChart(hourly_agg_div);
    hr_agg_chart.draw(hr_agg_data, hr_agg_options);


    // LINE CHART FOR DAILY DATA FOR ALL CAMPAIGNS
    var daily_data = new google.visualization.DataTable(); 

    daily_data.addColumn('date', 'Date');
    daily_data.addColumn('number', 'Visits');
    daily_data.addColumn('number', 'Clicks');
    daily_data.addColumn('number', 'Auths');
    daily_data.addColumn('number', 'Distinct Facebook Auths');
    daily_data.addColumn('number', '# Users Shown Friends');
    daily_data.addColumn('number', '# Users Who Shared');
    daily_data.addColumn('number', '# Friends Shared With');
    daily_data.addColumn('number', '# Distinct Friends Shared');
    daily_data.addColumn('number', 'Clickbacks');
    var daily_data_arr = new Array(); 
    for(j=0; j < daily_aggregate.data.length; j++)
    {
        var _date = [new Date(daily_aggregate.data[j][0], daily_aggregate.data[j][1], daily_aggregate.data[j][2])];
        _date = _date.concat(daily_aggregate.data[j].slice(3, daily_aggregate.data[j].length));
        daily_data_arr[j] = _date; 
    }
    daily_data.addRows(daily_data_arr);

    var daily_agg_div = document.createElement("div");
    daily_agg_div.id = "daily_agg_div";
    var daily_chart = new google.visualization.LineChart(daily_agg_div);
    daily_chart.draw(daily_data, {title: 'Daily Report(for the last 30 days)', fontSize: '10', enableInteractivity: 'true', 'width': 1000});




    // Add the div to the document that contains our Aggregate_Table
    var agg_title = document.createElement("p");
    agg_title.innerHTML = "Aggregate Data for All Campaigns";
    document.body.appendChild(agg_title);
    document.body.appendChild(agg_div);
    document.body.appendChild(document.createElement('br'));
    var today_title = document.createElement("p");
    today_title.innerHTML = "Data for All Campaigns for <b>{{today}}</b>";
    document.body.appendChild(today_title);
    document.body.appendChild(today_div);
    document.body.appendChild(hourly_agg_div);
    document.body.appendChild(daily_agg_div);
    document.body.appendChild(document.createElement('br'));
    document.body.appendChild(document.createElement('br'));
    document.body.appendChild(document.createElement('hr'));
    
    return
}



function mkEverything() {

    // create an array with our keys in it
    var all_keys = []
    for (name in all_json)
    {
        all_keys.push(name);
    }
 
    for(i = 0; i < all_keys.length; i++)
    {
        // for each key in our keys array create divs for the aggregate
        // and for the daily data
        var div = "aggregate_campaign_{0}";
        var div1 = "daily_campaign_{0}";
        var div2 = "hourly_campaign_{0}";
        var div3 = "monthly_campaign_{0}";

        // associate each div with the iteration we are on allowing
        // for a dynamic amount of divs to be created in turn
        // allowing for a dynamic number of tables and charts
        // to be displayed for our clients

        div = div.replace('{0}', i.toString());
        div1 = div1.replace('{0}', i.toString());
        div2 = div2.replace('{0}', i.toString());
        div3 = div3.replace('{0}', i.toString());
        var new_div = document.createElement("div");
        var new_div1 = document.createElement("div");
        var new_div2 = document.createElement("div");
        var new_div3 = document.createElement("div");
        new_div.id = div;
        new_div1.id = div1;
        new_div2.id = div2;
        //new_div2.style.width = "800px";

        new_div3.id = div3;
        //new_div3.style.width = "800px";

        // The div we just created for this campaign is the div
        // we will use to create our data table
        var data = new google.visualization.DataTable();
        data.addColumn('number', 'Visits');
        data.addColumn('number', 'Clicks');
        data.addColumn('number', 'Authorizations');
        data.addColumn('number', 'Distinct Authorized Facebook Users');
        data.addColumn('number', '# Users Shown Friends');
        data.addColumn('number', '# Users Who Shared');
        data.addColumn('number', '# Friends Shared With');
        data.addColumn('number', '# Distint Friends Shared');
        data.addColumn('number', 'Clickbacks');
        //var title = {title: keys[i]};
        var this_data = all_json[all_keys[i]].slice(1,all_json[all_keys[i]].length);
        data.addRows([this_data]);
        var table = new google.visualization.Table(new_div);
        table.draw(data, {title: all_keys[i]});

        var data1 = new google.visualization.DataTable();
        data1.addColumn('number', 'Visits');
        data1.addColumn('number', 'Clicks');
        data1.addColumn('number', 'Authorizations');
        data1.addColumn('number', 'Distinct Authorized Facebook Users');
        data1.addColumn('number', '# Users Shown Friends');
        data1.addColumn('number', '# Users Who Shared');
        data1.addColumn('number', '# Friends Shared With');
        data1.addColumn('number', '# Distint Friends Shared');
        data1.addColumn('number', 'Clickbacks');
        var this_data1 = day_json[all_keys[i]].slice(1,day_json[all_keys[i]].length); 
        data1.addRows([this_data1]);
        var table1 = new google.visualization.Table(new_div1);
        table1.draw(data1, {title: all_keys[i]});


        // Line Charts for hourly graphs using the the hourly_json object
        // we defined from above
        var line1_array = new Array();
        line1_array[0] = ['Hour', 'Visits', 'Clicks', 'Authorizations', 'Distinct Authorized Facebook Users', '# Users Shown Friends', '# Users Who Shared', '# Friends Shared With', '# Distinct Friends Shared', 'Clickbacks'];
        for(w=0; w < hourly_json[all_keys[i]].length; w++)
        {
            line1_array[w+1] = hourly_json[all_keys[i]][w];
        }
        var line1_chart_data = google.visualization.arrayToDataTable(line1_array);
        var line1_options = {title: 'Hourly Report', fontSize: '10', enableInteractivity: 'true', 'width': 1000};
        var line1 = new google.visualization.LineChart(new_div2);
        line1.draw(line1_chart_data, line1_options);


        // Line Chart for the monthly graphs using the monthly_json
        // Object we defined at the top

        var line2 = new google.visualization.DataTable();
        line2.addColumn('date', 'Date');
        line2.addColumn('number', 'Visits');
        line2.addColumn('number', 'Clicks');
        line2.addColumn('number', 'Auths');
        line2.addColumn('number', 'Distinct Facebook Auths');
        line2.addColumn('number', '# Users Shown Friends');
        line2.addColumn('number', '# Users Who Shared');
        line2.addColumn('number', '# Friends Shared With');
        line2.addColumn('number', '# Distinct Friends Shared');
        line2.addColumn('number', 'Clickbacks');
        var arr2 = new Array();
        
        for(j=0; j < monthly_json[all_keys[i]].length; j++)
        {
            var date_bits = monthly_json[all_keys[i]][j][0].split(/\D/);
            var _date = [new Date(date_bits[0], date_bits[1]-1, date_bits[2])];
            arr2[j] = _date.concat(monthly_json[all_keys[i]][j].slice(1, monthly_json[all_keys[i]][j].length));
        
        }

        line2.addRows(arr2);
        var line2opt = {title: 'Daily Report(for last 30 days)', fontSize: '10', 'width': 1000};
        var chart2 = new google.visualization.LineChart(new_div3);
        chart2.draw(line2, line2opt);
            


        // Adding all non-existent titles to their respective tables/charts
        // After adding the titles binding the div elements that contain our tables
        // and line charts to the html DOM.

        var title = document.createElement('p');
        title.innerHTML = '<h3>' + all_keys[i] + '</h3>';
        var all_data_disclaimer = document.createElement('p');
        all_data_disclaimer.innerHTML = "Data From Beginning of Campaign to <b>{{today}}</b>";
        var day_data_disclaimer = document.createElement('p');
        day_data_disclaimer.innerHTML = "Data for <b>{{today}}</b>";
       
        document.body.appendChild(title);
        document.body.appendChild(all_data_disclaimer);
        document.body.appendChild(new_div);
        document.body.appendChild(day_data_disclaimer);
        document.body.appendChild(new_div1);
        document.body.appendChild(new_div2);
        document.body.appendChild(new_div3);
        document.body.appendChild(document.createElement('hr'));
        document.body.appendChild(document.createElement('br'));
        document.body.appendChild(document.createElement('br'));
      
    }
    
}



function mkCampaigns() {

    // campaign chooser


    /* 
    // create the first second that lists out our campaigns for this client
    var client = document.createElement('p');
    client.innerHTML = 'Campaigns Currently Running for <b>{{client_name}}</b>';
    var items = document.createElement('ul');
    console.log(all_keys);
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
