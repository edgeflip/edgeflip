$(function() {
  $("#mailing-group-list").hide();
  
  $( "#groups" ).sortable({
    connectWith: "#models",
    start: function(){
      $('#models').addClass('droppable')
    },
    stop: function(){
      $('#models').removeClass('droppable')
    }
  });
  $( "#models" ).sortable({
    connectWith: "#smart-lists",
    start: function(){
      $('#smart-lists').addClass('droppable')
    },
    stop: function(){
      $('#smart-lists').removeClass('droppable')
    },
    receive: function(event, ui){
      var group_id = ui.item.attr('data-id');
      ui.item.clone().prependTo($(this))
      ui.sender.sortable('cancel');
      $.ajax({
               type: "POST",
               url: '/create_model',
               dataType: 'json',
               contentType: "application/json",
               //json object to sent to the authentication url
               data: JSON.stringify({model_name: "Based on "+group_id, mailing_group:group_id}),
               success: function () {
                 
               }
        });
      
      
      
    }
  });
  
  $.getJSON('/models', function(data){
     var template = $('#models-template').html();
     $('#models').html(Mustache.to_html(template,data));
  });

  $.getJSON('/groups',function(data){
    var template = $('#groups-template').html();
    $('#groups').html(Mustache.to_html(template,data));
  });

  

});

$('a[href="#basic"]').on('show', function(e){
  $("#mailing-group-list").animate({width: 'hide'});
});

$('a[href="#advanced"]').on('show', function(e){
  $("#mailing-group-list").animate({width: 'show'});
})

$('body').on('click','#btn-cancel', function(e){
  $(e.currentTarget).parents('li').remove();
  return false;
})

$('body').on('click','#btn-create', function(e){
  var item = $(e.currentTarget).parents('li');
  var size = item.find('#size').val();
  var model_id = item.attr('data-id');
  
  item.find('form').remove();
  item.addClass('building');

  data = {'size':size/100.0};

  $.ajax({
    type: "POST",
    url: '/models/'+model_id+'/cut',
    dataType: 'json',
    contentType: "application/json",
    //json object to sent to the authentication url
    data: JSON.stringify(data),
    success: function (data) {
     t = setInterval(function(){
       $.get('/tasks/' + data.task_id + '/state',function(task){
         if(task.state == 'SUCCESS'){
           item.removeClass('building');
           clearTimeout(t);
         }else if (task.state == 'FAILURE'){
           item.removeClass('building');
           item.addClass('failure');
           clearTimeout(t);
         }
       })
     }, 2000);
    }
  });

  
  return false;
})


// Create cons group
$( "#smart-lists" ).sortable({
  receive: function(event, ui){
    ui.sender.sortable('cancel');
    var model_id = ui.item.attr('data-id');
    //var item = ui.item.clone();
    var data = {model_id: model_id};
    var item = $(Mustache.to_html($('#cons-item-template').html(),data));
              
    item.prependTo($(this));

  }
  
});
