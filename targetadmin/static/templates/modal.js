define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  


  return "<div data-js=\"modalContainer\" class=\"modal fade\" id=\"theModal\" tabindex=\"-1\" role=\"dialog\" aria-labelledby=\"myModalLabel\" aria-hidden=\"true\"><div class=\"modal-dialog\"><div class=\"modal-content\"><div class=\"modal-header\"><button type=\"button\" class=\"close\" data-dismiss=\"modal\"><span aria-hidden=\"true\">X</span><span class=\"sr-only\">Close</span></button><h4 class=\"modal-title\" id=\"myModalLabel\" data-js=\"modalTitle\"></h4></div><div class=\"modal-body\" data-js=\"modalBody\"></div><div class=\"modal-footer\"><button type=\"button\" class=\"btn btn-default hide\" data-dismiss=\"modal\">Close</button><button type=\"button\" class=\"btn\" data-js=\"confirmBtn\">Save changes</button></div></div></div></div>";
  })

});