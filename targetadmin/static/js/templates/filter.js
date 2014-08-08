(function() {
  var template = Handlebars.template, templates = Handlebars.templates = Handlebars.templates || {};
templates['filter'] = template({"compiler":[5,">= 2.0.0"],"main":function(depth0,helpers,partials,data) {
  var helper, functionType="function", escapeExpression=this.escapeExpression;
  return "<div title=\""
    + escapeExpression(((helper = helpers.feature || (depth0 && depth0.feature)),(typeof helper === functionType ? helper.call(depth0, {"name":"feature","hash":{},"data":data}) : helper)))
    + " "
    + escapeExpression(((helper = helpers.operator || (depth0 && depth0.operator)),(typeof helper === functionType ? helper.call(depth0, {"name":"operator","hash":{},"data":data}) : helper)))
    + " "
    + escapeExpression(((helper = helpers.value || (depth0 && depth0.value)),(typeof helper === functionType ? helper.call(depth0, {"name":"value","hash":{},"data":data}) : helper)))
    + "\"\n     data-filter-id=\"set_number="
    + escapeExpression(((helper = helpers.feature || (depth0 && depth0.feature)),(typeof helper === functionType ? helper.call(depth0, {"name":"feature","hash":{},"data":data}) : helper)))
    + "."
    + escapeExpression(((helper = helpers.operator || (depth0 && depth0.operator)),(typeof helper === functionType ? helper.call(depth0, {"name":"operator","hash":{},"data":data}) : helper)))
    + "."
    + escapeExpression(((helper = helpers.value || (depth0 && depth0.value)),(typeof helper === functionType ? helper.call(depth0, {"name":"value","hash":{},"data":data}) : helper)))
    + "\" class=\"span2 draggable\">\n     <div class=\"filter-content-container\">\n         <span class=\"filter\">"
    + escapeExpression(((helper = helpers.readable || (depth0 && depth0.readable)),(typeof helper === functionType ? helper.call(depth0, {"name":"readable","hash":{},"data":data}) : helper)))
    + "</span>\n     </div>\n</div>\n";
},"useData":true});
})();