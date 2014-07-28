define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = "", stack1, helper;
  buffer += "\n            <div class=\"audience-label\">";
  if (helper = helpers.label) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.label); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</div>\n            <ul>\n                ";
  stack1 = helpers.each.call(depth0, (depth0 && depth0.feature), {hash:{},inverse:self.noop,fn:self.program(2, program2, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n            </ul>\n        ";
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = "";
  buffer += "\n                    <li>"
    + escapeExpression((typeof depth0 === functionType ? depth0.apply(depth0) : depth0))
    + "</li>\n                ";
  return buffer;
  }

  buffer += "<section id=\"campaign-summary\" class=\"col-md-8 col-md-offset2\">\n    <h2 class=\"page-header\">Campaign Summary</h2>\n    <h4 class=\"campaign-name\">";
  if (helper = helpers.name) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.name); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</h4>\n    <div class=\"well\">\n        <h6>Audience</h6>\n        ";
  stack1 = helpers.each.call(depth0, (depth0 && depth0.filter), {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n    </div>\n    <div class=\"well\">\n        <section id=\"faces-example\"></section>\n    </div>\n    <div class=\"well\">\n        <section id=\"fb-obj-example\"></section>\n    </div>\n</section>\n";
  return buffer;
  })

});