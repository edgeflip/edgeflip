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

    // toggle for logarithmic scaling
    window.logscale = false;
    $('#logscale').button().click( function () {
        window.logscale = window.logscale ? false:true;
        $('#logscale').button( "option", "label", "Logarithmic Scaling: "+(window.logscale? "On":"Off"));
        draw();
        });
    }


function getData() {
    // no need to post client, the server can pick that out of whatever user
    day = $.datepicker.formatDate('mm/dd/yy', $('#datepicker').datepicker('getDate'));
    campaign = $('#campaignpicker select').val();
    $.post('/dashboard/chartdata/', {'campaign':campaign, 'day':day}, onData);
    }


function onData(response) {
    window.response = response;

    // reset valid dates in the jquery widget
    $('#datepicker').datepicker( "option", "minDate", response.minday);
    $('#datepicker').datepicker( "option", "maxDate", response.maxday);


    // update data tables
    window.dailydata = new google.visualization.DataTable({'cols':response.daily_cols, 'rows':response.daily});
    window.monthlydata = new google.visualization.DataTable({'cols':response.monthly_cols, 'rows':response.monthly});


    // format dates
    var shortdate = new google.visualization.DateFormat({formatType: 'short'});
    shortdate.format( monthlydata, 0); 

    var shorthour = new google.visualization.DateFormat({formatType: 'HH'});
    shorthour.format( dailydata, 0);

    draw();
    }



function draw() {

    // redraw charts
    var dailyopts = {
        title: 'Hourly Volume - '+window.response.dailyday, 
        enableInteractivity: 'true', 
        width: 580, 
        height:175,
        chartArea: {width:500},
        lineWidth: 1, // set this a bit thinner than monthly 

        // curveType: 'function', // nice curves but it messes up vaxis calcs
        legend: {position: 'none'}, // kill this legend, we'll hack into the bigger one below
        // "turn off" the gridlines, but keep unit labels on axes
        vAxis: {gridlines: {color:'#FFF'} },
        hAxis: {gridlines: {color:'#FFF', count:13}, format:'H'},
        };

    window.dailychart.draw(window.dailydata, dailyopts);

    window.monthlychart.draw(window.monthlydata, {
        title: 'Daily Volume '+response.minday+' - '+response.maxday, 
        enableInteractivity: 'true', 
        chartArea:{left:50,},
        width: 799,
        height:250,
        legend: {position: 'right', textStyle: {fontSize:10}, alignment: 'end'},

        // "turn off" the gridlines, but keep unit labels on axes
        vAxis: {gridlines: {color:'#FFF'}, logScale:window.logscale},
        hAxis: {gridlines: {color:'#FFF', count:7}, format:'M/dd'},
        });
    }


