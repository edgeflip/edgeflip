function flash(title, msg){
  var alert = $('<div class="alert alert-info fade in">' +
    ' <a class="close" data-dismiss="alert">×</a>' +
    ' <strong>'+title+'</strong> '+ msg + 
    '</div>').prependTo('.content');
  setTimeout(function(){
    alert.alert('close');
  }, 5000);
  
}

$("a[rel=popover]")
      .popover()
      .click(function(e) {
        e.preventDefault()
      });


/* Listing models and cutting lists from them */
$('a[href="#models"]').on('show', function(e){
  $('#model-list').html('loading...');
  $.getJSON('/models', function(data){
     var template = $('#table-template').html();
     data['row_class'] = "mailing";
     var t = $('#model-list').html(Mustache.to_html(template,data));
     t.find('tbody tr').append($('<td><i class="icon-download-alt"></i><a href="#cut">Cut</a>'))
  });   
})

$('#model-list').on('click','a[href="#cut"]',function(e){
  
  var model_id = $(e.currentTarget).parent().parent().children(':first-child').text();
  $('#cutting-options').data('based_on', model_id);
  $('#cutting-options').modal();
  return false;
});

$('#cut-btn').on('click',  function(e){
 
  var model_id =  $('#cutting-options').data('based_on');
 
  $.ajax({
          type: "GET",
          url: '/models/'+model_id+'/cut',
          dataType: 'json',
          contentType: "application/json",
          //json object to sent to the authentication url
          //data: JSON.stringify({model_name: model_name, mailing_group: mailing_group}),
          success: function () {
            flash('Cutting the list', 'this could take awhile.');
          }
      });

  //return false;
});

/* Listing mailing groups and creating models */
$('a[href="#train"]').on('show', function (e) {
  $('#train').html('loading...');
  $.getJSON('/execute', {'q':"SELECT distinct row_id AS mailing_id, tag AS mailing_tag "+
          "FROM bsd.tag__row "+
          "WHERE "+
          "  realm = 'maillist' AND table_name = 'mailing' AND "+
          "  tag like 'mg.%' AND "+
          "  row_id IN ( "+
          "    SELECT distinct row_id FROM bsd.tag__row WHERE "+
          "      realm = 'maillist' AND table_name = 'mailing'"+ 
          "      AND lower(tag) like 'contrib_page.%' "+
          "      AND row_id >= 13020 "+
          "      AND row_id NOT IN ( "+
          "        SELECT distinct row_id FROM bsd.tag__row "+
          "        WHERE realm = 'maillist' AND table_name = 'mailing' AND lower(tag) like 'signup_page.%'"+
          "      )"+
          "  );"},
    function(data){
      var template = $('#table-template').html();
      data['row_class'] = "mailing";
      var t = $('#train').html(Mustache.to_html(template,data));
      t.find('tbody tr').append($('<td><i class="icon-list"></i><a href="#build">Build</a> <i class="icon-pencil"></i><a href="#model" >Model</a></td>'))
  });
});




$('#train').on('click','a[href="#build"]',function(e){
  
  var mailing_id = $(e.currentTarget).parent().parent().children(':nth-child(2)').text();

  $.ajax({
          type: "POST",
          url: '/build_data_set',
          dataType: 'json',
          contentType: "application/json",
          //json object to sent to the authentication url
          data: JSON.stringify({mailing_id: mailing_id}),
          success: function () {
            flash('Started building the list', 'this could take awhile.');
          }
      });

  return false;
});

$('#train').on('click','a[href="#model"]',function(e){
  
  var mailing_id = $(e.currentTarget).parent().parent().children(':nth-child(2)').text();
  $('#training-options').data('based_on', mailing_id);
  $('#training-options').modal();
  
  return false;
});

// Start training when a user clicks train
$('#train-btn').on('click',  function(e){
 
  var model_name = $('#model-name').val(),
      mailing_group =  $('#training-options').data('based_on');
 
  $.ajax({
          type: "POST",
          url: '/create_model',
          dataType: 'json',
          contentType: "application/json",
          //json object to sent to the authentication url
          data: JSON.stringify({model_name: model_name, mailing_group: mailing_group}),
          success: function () {
            flash('Started building the list', 'this could take awhile.');
          }
      });

  return false;
});

/* Inspecting the current task queue */
$('a[href="#tasks"]').on('show', function (e) {
  $('#tasks').html('inspecting queues...');
  $.getJSON('/tasks', 
    function(data){
      var template = $('#tasks-template').html();
      console.log('flatening')
      data = _.flatten(_.values(data), true);
      $('#tasks').html(Mustache.to_html(template,data));
  });
});


/* Startup */
$(function () {
  //TODO: figure out a way to trigger the first tab's show even w/o having
  // to show some other tab first
  $('.nav-tabs a:last').tab('show')
  $('.nav-tabs a:first').tab('show');
})
