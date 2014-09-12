define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  
  return "disabled=\"true\"";
  }

function program3(depth0,data) {
  
  
  return "<span class=\"glyphicon glyphicon-remove\" data-js=\"removeLayerBtn\"></span>";
  }

  buffer += "<div class=\"filter-layer\" data-js=\"filterLayer\"><div class=\"filter-layer-header\"><span data-target=\"filterLabel\" class=\"filter-layer-label\">";
  if (helper = helpers.label) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.label); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</span><button data-js=\"addFallbackBtn\" type=\"button\" class=\"btn\" ";
  stack1 = helpers['if'].call(depth0, (depth0 && depth0.disableAddBtn), {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += ">            Add Fallback Audience        </button>        ";
  stack1 = helpers['if'].call(depth0, (depth0 && depth0.removeBtn), {hash:{},inverse:self.noop,fn:self.program(3, program3, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "    </div><div data-js=\"filterContainer\" class=\"filter-container\" data-type=\"sortable\"></div><input data-target=\"filterLayerFormField\" type=\"hidden\" name=\"enabled-filters-";
  if (helper = helpers.count) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.count); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\" /></div>";
  return buffer;
  })

});