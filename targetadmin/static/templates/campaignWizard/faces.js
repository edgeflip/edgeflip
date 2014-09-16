define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression;


  buffer += "<section class=\"row campaign-wizard-faces image-companion\"><div class=\"col-sm-12\"><h1 data-js=\"heading\" class=\"heading\"><span>Create Friend Suggestion Page For </span><span data-js=\"campaignName\">";
  if (helper = helpers.name) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.name); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</span></h1><hr class=\"heading-separator\"><div class=\"row subheader\"><div class=\"col-sm-8\"><span>The Friend Suggestion Page is what your supporters will see after they authorize the Targeted Sharing application to access their Facebook information. They'll use this page to choose which friends to share with. Configure your Friend Suggestion Page by filling in the form below.</span><a href=\"";
  if (helper = helpers.howItWorksURL) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.howItWorksURL); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\" target=\"_blank\"> Learn More.</a></div></div><div class=\"row\"><div class=\"col-sm-5 input-container\" data-js=\"inputContainer\"><div class=\"form-group\"><label class=\"input-label\">Headline</label><input class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\" name=\"sharing_prompt\" type=\"text\" placeholder=\"Your Headline Here\"><span class=\"glyphicon glyphicon-remove form-control-feedback hide\"></span></div><div class=\"form-group\"><label class=\"input-label\">Sub-heading</label><span>(optional)</span><textarea class=\"form-control\" data-js=\"formInput\" data-type=\"optional\" name=\"sharing_sub_header\" rows=\"8\" placeholder=\"Your Sub-heading Here\"></textarea></div><div class=\"form-group\"><label class=\"input-label\">Sharing Button</label><input class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\" name=\"sharing_button\" type=\"text\" placeholder=\"Show Your Support\"><span class=\"glyphicon glyphicon-remove form-control-feedback hide\"></span></div><div class=\"form-group\"><label class=\"input-label\">Thanks URL</label><input class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\" name=\"thanks_url\" type=\"text\" placeholder=\"http://your.org/thanks.html\"><span class=\"glyphicon glyphicon-remove form-control-feedback hide\"></span></div><div class=\"form-group\"><label class=\"input-label\">Error URL</label><input class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\" name=\"error_url\" type=\"text\" placeholder=\"http://your.org/oops.html\"><span class=\"glyphicon glyphicon-remove form-control-feedback hide\"></span></div><div class=\"nav-button-container clearfix\"><button type=\"button\" class=\"btn pull-right\" data-js=\"nextStep\">Next Step</button><button type=\"button\" class=\"btn pull-right back-btn\" data-js=\"prevStep\">Go Back</button></div></div><div class=\"col-sm-7\"><div data-js=\"imageContainer\" class=\"image-container\"><img data-js=\"companionImage\" src=\"";
  if (helper = helpers.facesExampleURL) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.facesExampleURL); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\"></div></div><div data-js=\"popoverEl\" class=\"popover-target\"></div></div></div></section>";
  return buffer;
  })

});