define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression;


  buffer += "<section class=\"col-sm-10 help\">\n    <img src=\"";
  if (helper = helpers.howItWorksSrc) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.howItWorksSrc); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\">\n    <div class=\"contact\">\n        <span>If you have more questions, feel free to </span>\n        <a href=\"mailto:help@edgeflip.com\" target=\"_blank\">contact us</a>\n    </div>\n</section>\n";
  return buffer;
  })

});