
window.onload = init

function init() {
    // first pageview, get data for newest campaign and draw a chart
    getData();

    // load up datepicker widgets
    $( "#datepicker" ).datepicker({gotoCurrent:true, onSelect:getData});

    window.R = Raphael("daily");

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

    window.data = JSON.parse(response.fakedaily);
    draw();

    }


function draw() {
    R.clear();
    R.rect(0,0,R.width,R.height);
    // so vgutter is the space between the bars and the top/bottom of the chart
    // gutter is the space horizontally between the bars
    window.dailychart = R.barchart(0,0,R.width,R.height, data, {stacked: true,type:'hard', vgutter:20});
    }

function mkBars() {
    for (i=1,i<24,i++) {
    
        for (thing in data) {
            // R.rect( data[thing].pop())}
            // draw a rect at offset+i*width with a height of data[thing].pop()
            }

        }
