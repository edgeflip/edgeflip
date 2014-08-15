define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, functionType="function", escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "                <li role=\"presentation\"><a data-js=\"filterType\" data-type=\""
    + escapeExpression(((stack1 = (depth0 && depth0.name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\" role=\"menuitem\" tabindex=\"-1\" href=\"#\">"
    + escapeExpression(((stack1 = (depth0 && depth0.label)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</a></li>            ";
  return buffer;
  }

  buffer += "<section id=\"add-filter\"><div class=\"dropdown\"><button class=\"btn btn-default dropdown-toggle\" type=\"button\" id=\"filter-type\" data-toggle=\"dropdown\"><span class=\"pull-left\">Select Filter Type</span><span class=\"caret\"></span></button><ul class=\"dropdown-menu\" role=\"menu\" aria-labelledby=\"filter-type\">            ";
  stack1 = helpers.each.call(depth0, (depth0 && depth0.filterTypes), {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "        </ul></div><div data-js=\"filterTypeUI\" data-type=\"age\" class=\"hide\"><div class=\"age-range-display\" data-js=\"ageRangeDisplay\"></div><div class=\"age-slider\" data-js=\"ageSlider\"></div></div><div data-js=\"filterTypeUI\" data-type=\"gender\" class=\"dropdown hide\"><button class=\"btn btn-default dropdown-toggle\" type=\"button\" id=\"interest-type\" data-toggle=\"dropdown\"><span>Select Gender</span><span class=\"caret\"></span></button><ul class=\"dropdown-menu\" role=\"menu\" aria-labelledby=\"interest-type\"><li role=\"presentation\"><a data-js=\"genderType\" data-type=\"female\" role=\"menuitem\" tabindex=\"-1\" href=\"#\">Female</a></li><li role=\"presentation\"><a data-js=\"genderType\" data-type=\"male\" role=\"menuitem\" tabindex=\"-1\" href=\"#\">Male</a></li></ul></div><div data-js=\"filterTypeUI\" data-type=\"interest\" class=\"dropdown hide\"><button class=\"btn btn-default dropdown-toggle\" type=\"button\" id=\"interest-type\" data-toggle=\"dropdown\"><span>Select Interest Type</span><span class=\"caret\"></span></button><ul class=\"dropdown-menu\" role=\"menu\" aria-labelledby=\"interest-type\"><li role=\"presentation\"><a data-js=\"interestType\" data-type=\"cycling\" role=\"menuitem\" tabindex=\"-1\" href=\"#\">Cycling</a></li><li role=\"presentation\"><a data-js=\"interestType\" data-type=\"education\" role=\"menuitem\" tabindex=\"-1\" href=\"#\">Education</a></li><li role=\"presentation\"><a data-js=\"interestType\" data-type=\"healthcare\" role=\"menuitem\" tabindex=\"-1\" href=\"#\">Healthcare</a></li></ul></div><div data-js=\"filterTypeUI\" data-type=\"location\" class=\"dropdown hide\"><div class=\"dropdown hide\"><button class=\"btn btn-default dropdown-toggle\" type=\"button\" id=\"location-type\" data-toggle=\"dropdown\"><span>Location Type (one per filter)</span><span class=\"caret\"></span></button><ul class=\"dropdown-menu\" role=\"menu\" aria-labelledby=\"interest-type\"><li role=\"presentation\"><a data-js=\"interestType\" data-type=\"cycling\" role=\"menuitem\" tabindex=\"-1\" href=\"#\">Cycling</a></li><li role=\"presentation\"><a data-js=\"interestType\" data-type=\"education\" role=\"menuitem\" tabindex=\"-1\" href=\"#\">Education</a></li><li role=\"presentation\"><a data-js=\"interestType\" data-type=\"healthcare\" role=\"menuitem\" tabindex=\"-1\" href=\"#\">Healthcare</a></li></ul></div><input data-js=\"locationText\" class=\"form-control\" type=\"text\"><button class=\"btn add-location-btn\" data-js=\"addLocationBtn\">Add Location</button><div data-js=\"locationContainer\"></div></div></section>";
  return buffer;
  })

});