define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "        <li class=\"button\" data-nav=\""
    + escapeExpression(((stack1 = (depth0 && depth0.name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\" ";
  stack1 = helpers['if'].call(depth0, (depth0 && depth0.view), {hash:{},inverse:self.noop,fn:self.program(2, program2, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "><span class=\""
    + escapeExpression(((stack1 = (depth0 && depth0.glyphClass)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\"></span><span>"
    + escapeExpression(((stack1 = (depth0 && depth0.label)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</span></li>        ";
  return buffer;
  }
function program2(depth0,data) {
  
  
  return " data-js=\"contentBtn\"";
  }

  buffer += "<nav id=\"left-panel\" class=\"col-sm-2\"><ol><li class=\"logo\"><img src=\"";
  if (helper = helpers.logoSrc) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.logoSrc); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\"/></li>        ";
  stack1 = helpers.each.call(depth0, (depth0 && depth0.nav), {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "    </ol></nav>";
  return buffer;
  })

});