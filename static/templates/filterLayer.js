define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression;


  buffer += "<section data-js=\"layerContainer\">\n    <div class=\"clearfix\">\n        <h5 data-js=\"layerHeading\" class=\"layer-text-header pull-left\">Layer ";
  if (helper = helpers.layerNumber) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.layerNumber); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</h5>\n        <h5 data-js=\"removeLayerBtn\" class=\"btn btn-link pull-right remove-layer\">\n            <span class=\"glyphicon glyphicon-remove\">\n        </h5>\n    </div>\n    <div class=\"clearfix\">\n        <input type=\"hidden\" name=\"id_enabled-filters-";
  if (helper = helpers.layerNumber) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.layerNumber); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\" data-js=\"layerInput\">\n        <div class=\"col-md-12 well sortable target-well\">";
  if (helper = helpers.content) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.content); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "</div>\n    </div>\n</section>\n";
  return buffer;
  })

});