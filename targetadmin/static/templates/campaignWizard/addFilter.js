define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "                <li><a data-js=\"filterType\" data-type=\""
    + escapeExpression(((stack1 = (depth0 && depth0.name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\" tabindex=\"-1\">"
    + escapeExpression(((stack1 = (depth0 && depth0.label)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</a></li>            ";
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "        <div data-js=\"filterTypeUI\" data-type=\""
    + escapeExpression(((stack1 = (depth0 && depth0.name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\" class=\"sub-dropdown dropdown hide\"><button class=\"btn btn-default dropdown-toggle\" type=\"button\" data-toggle=\"dropdown\"><span data-js=\"dropdownLabel\" class=\"dropdown-label\">"
    + escapeExpression(((stack1 = (depth0 && depth0.label)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</span><span class=\"caret\"></span></button><ul class=\"dropdown-menu\">                ";
  stack1 = helpers.each.call(depth0, (depth0 && depth0.options), {hash:{},inverse:self.noop,fn:self.program(4, program4, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "            </ul></div>    ";
  return buffer;
  }
function program4(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "                    <li><a data-js=\"filterTypeOption\" data-value=\""
    + escapeExpression(((stack1 = (depth0 && depth0.value)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\"tabindex=\"-1\">"
    + escapeExpression(((stack1 = (depth0 && depth0.label)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</a></li>                ";
  return buffer;
  }

  buffer += "<section id=\"add-filter\"><div class=\"dropdown\"><button class=\"btn btn-default dropdown-toggle\" type=\"button\" data-toggle=\"dropdown\"><span data-js=\"dropdownLabel\" class=\"dropdown-label\">";
  if (helper = helpers.filterTypeLabel) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.filterTypeLabel); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</span><span class=\"caret\"></span></button><ul class=\"dropdown-menu\">            ";
  stack1 = helpers.each.call(depth0, (depth0 && depth0.filterTypes), {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "        </ul></div><div data-js=\"filterTypeUI\" data-type=\"age\" class=\"hide\"><div class=\"age-range-display\" data-js=\"ageRangeDisplay\"></div><div class=\"age-slider\" data-js=\"ageSlider\"></div></div>    ";
  stack1 = helpers.each.call(depth0, (depth0 && depth0.filterTypeOptions), {hash:{},inverse:self.noop,fn:self.program(3, program3, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "    <div data-js=\"filterTypeUI\" data-type=\"location\" class=\"hide\"><div class=\"sub-dropdown dropdown\"><button class=\"btn btn-default dropdown-toggle\" type=\"button\" data-toggle=\"dropdown\"><span data-js=\"dropdownLabel\" class=\"dropdown-label\">Location Type (one per filter)</span><span class=\"caret\"></span></button><ul class=\"dropdown-menu\"><li><a data-js=\"locationTypeOption\" data-value=\"city\" tabindex=\"-1\">City</a></li><li><a data-js=\"locationTypeOption\" data-value=\"state\" tabindex=\"-1\">State</a></li></ul></div><input placeholder=\"Select City\" data-type=\"city\" data-js=\"locationInput\" class=\"hide form-control location-text\" type=\"text\"><input placeholder=\"Select State\" data-type=\"state\" data-js=\"locationInput\" class=\"hide form-control location-text\" type=\"text\"><button class=\"btn add-location-btn\" data-js=\"addLocationBtn\">Add Filter</button><ul class=\"location-container clearfix hide\" data-js=\"locationContainer\"></ul></div></section>";
  return buffer;
  })

});