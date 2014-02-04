$(document).ready(init);

function init() {
    console.log('init');

    $('#submitter').click(function() { query();return false;});

    }

function query () {
    $('#data').children().remove();
    var csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
    $.post('/reporting/edgeplorer/', {'fbid':$('#fbid').val(), 'csrfmiddlewaretoken':csrfToken}, on_data).fail(on_fail);

    }

function on_fail(response) {
    console.log('fail');
    alert('Error message: ' + response.responseText);
    }

function on_data(response) {
    window.response = response;  // unnecessary but handy for debugging

    function tablify (table, dataset) {
    
        var thead = table.append('thead').append('tr');
        var keys = thead.selectAll('th').data( d3.keys(dataset[0]))
            .enter()
            .append('th')
            .text( function(d) {return d;});
    
        var tbody = table.append('tbody');
        var rows = tbody.selectAll('tr').data(dataset)
            .enter()
            .append('tr');
    
        var cells = rows.selectAll('td').data(
            function(row) { return d3.keys(dataset[0]).map( function(col) {return row[col];}); })
            .enter()
            .append('td')
            .text( function(d) {return d;});
        }

    // USER TABLE
    var usertable = d3.select('#data').append('table').attr('id', 'usertable');
    tablify( usertable, response.users);

    // EVENTS TABLE
    var eventstable = d3.select('#data').append('table').attr('id', 'eventstable');
    tablify( eventstable, response.events);

    // EDGES TABLE
    var edgestable = d3.select('#data').append('table').attr('id', 'edgestable');
    tablify( edgestable, response.edges);
    }



