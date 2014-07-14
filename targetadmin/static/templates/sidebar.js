define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression;


  buffer += "<nav id=\"left-panel\" class=\"col-sm-2\">\n    <ol>\n        <li class=\"logo\">\n            <img src=\"";
  if (helper = helpers.logoSrc) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.logoSrc); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\"/>\n        </li>\n        <li class=\"home-btn\" data-js=\"btn\" data->\n            <span class=\"glyphicon glyphicon-home\"></span>\n            <span class=\"client-name\">";
  if (helper = helpers.clientName) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.clientName); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</span>\n        </li>\n        <li class=\"campaign-btn\" data-js=\"btn\">\n            <span class=\"glyphicon glyphicon-share\"></span>\n            <span class=\"client-name\">Campaigns</span>\n        </li>\n        <li class=\"report-btn\" data-js=\"btn\">\n            <span class=\"glyphicon glyphicon-stats\"></span>\n            <span class=\"client-name\">Reports</span>\n        </li>\n        <li class=\"help-btn\" data-js=\"btn\">\n            <span class=\"glyphicon glyphicon-info-sign\"></span>\n            <span class=\"client-name\">Help</span>\n        </li>\n    </ol>\n</nav>\n";
  return buffer;
  })

});