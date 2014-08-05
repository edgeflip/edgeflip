define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression;


  buffer += "<nav id=\"left-panel\" class=\"col-sm-2\"><ol><li class=\"logo\"><img src=\"";
  if (helper = helpers.logoSrc) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.logoSrc); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\"/></li><li><span class=\"glyphicon glyphicon-home\"></span><span>";
  if (helper = helpers.clientName) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.clientName); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</span></li><li class=\"button\" data-js=\"btn\" data-nav=\"campaigns\"><span class=\"glyphicon glyphicon-share\"></span><span>Campaigns</span></li><li class=\"button\" data-nav=\"reports\"><span class=\"glyphicon glyphicon-stats\"></span><span>Reports</span></li><li class=\"button\" data-js=\"btn\" data-nav=\"help\"><span class=\"glyphicon glyphicon-info-sign\"></span><span>Help</span></li><li class=\"button\" data-js=\"btn\" data-nav=\"widgets\"><span class=\"glyphicon glyphicon-certificate\"></span><span>Widgets</span></li></ol></nav>";
  return buffer;
  })

});