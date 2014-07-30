define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression;


  buffer += "<section id=\"campaign-summary\" class=\"col-md-8 col-md-offset2\">\n    <h2 class=\"page-header\">Campaign Summary</h2>\n    <h4 class=\"campaign-name\">";
  if (helper = helpers.name) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.name); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</h4>\n    <div class=\"well\">\n        <h6>Audience</h6>\n        <section data-js=\"filterContainer\"></div>\n    </div>\n    <div class=\"well\">\n        <h6>Faces Page</h6>\n        <section data-js=\"facesContainer\"></section>\n    </div>\n    <div class=\"well\">\n        <h6>Facebook Post</h6>\n        <section data-js=\"fbPostExample\"></section>\n    </div>\n</section>\n";
  return buffer;
  })

});