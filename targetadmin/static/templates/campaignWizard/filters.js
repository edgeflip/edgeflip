define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  
  return "checked=\"checked\" ";
  }

  buffer += "<section class=\"row campaign-wizard-filters\"><div class=\"col-sm-12\"><h1 data-js=\"heading\" class=\"heading\"><span>Select A Target Audience For </span><span data-js=\"campaignName\">";
  if (helper = helpers.name) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.name); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</span></h1><hr class=\"heading-separator\"><div class=\"row subheader\"><div class=\"col-sm-8\"><span>Define a Target Audience for your campaign by dragging one or more filters from the Available Filters container to the Enabled Filters container. You can also add up to four Fallback Audiences with fewer filters enabled by clicking \"Add Fallback Audience.\"</span><button data-js=\"moreInfoBtn\" type=\"button\" class=\"btn btn-link\">Learn more about audiences.</button></div></div><div class=\"row\"><div class=\"col-sm-9\"><div class=\"title\">Enabled Filters</div><div data-js=\"enabledFiltersContainer\" class=\"enabled-filters\"></div><div class=\"available-filters-header\"><span class=\"title\">Available Filters</span><button type=\"button\" class=\"btn\" data-js=\"addFilterBtn\">Add Filter</button></div><div data-js=\"availableFilters\" class=\"available-filters filter-container clearfix\" data-type=\"sortable\"></div><div><span>Include empty fallback</span><input ";
  stack1 = helpers.unless.call(depth0, (depth0 && depth0.noEmptyFallback), {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "class=\"empty-fallback-input\" data-js=\"formInput\" name=\"include_empty_fallback\" type=\"checkbox\"><span class=\"glyphicon glyphicon-question-sign\" data-js=\"emptyFallbackHelpBtn\"></span></div><div><button type=\"button\" class=\"btn pull-right\" data-js=\"nextStep\">Next Step</button><button type=\"button\" class=\"btn pull-right back-btn\" data-js=\"prevStep\">Go Back</button></div></div></div></div></section>";
  return buffer;
  })

});