define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression;


  buffer += "<section class=\"row campaign-wizard-fb-obj image-companion\"><div class=\"col-sm-12\"><h1 data-js=\"heading\" class=\"heading\"><span>Create Friend Suggestion Page For </span><span data-js=\"campaignName\">";
  if (helper = helpers.name) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.name); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</span></h1><hr class=\"heading-separator\"><div class=\"row subheader\"><div class=\"col-sm-8\"><span>Once your supporters have selected which friends to share with, the Targeted Sharing application will generate a Facebook post that your target audience will see. Configure your Facebook post by filling in the form below.</span><a href=\"";
  if (helper = helpers.howItWorksURL) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.howItWorksURL); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\" target=\"_blank\"> Learn More.</a></div></div><div class=\"row\"><div class=\"col-sm-5 input-container\" data-js=\"inputContainer\"><div class=\"form-group\"><label class=\"input-label\">Cause or Organization Being Supported</label><input class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\" name=\"org_name\" type=\"text\" placeholder=\"Your Cause\"><span class=\"glyphicon glyphicon-remove form-control-feedback hide\"></span></div><div class=\"form-group\"><label class=\"input-label\">Suggested Messages</label><div>Help your supporters craft the perfect Facebook post by suggesting two sample messages.</div></div><div class=\"form-group\"><div class=\"message-heading\">Message 1</div><label class=\"message-label\">Text before friend names (optional)</label><input class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\"                           data-type=\"optional\" name=\"msg1_pre\" type=\"text\" placeholder=\"Hi\"></div><div class=\"form-group\"><label class=\"message-label\">Text after friend names (optional)</label><input class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\"                           data-type=\"optional\" name=\"msg1_post\" type=\"text\" placeholder=\"-- this is a suggested message.\"></div><div class=\"form-group\"><div class=\"message-heading\">Message 2</div><label class=\"message-label\">Text before friend names (optional)</label><input class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\"                           data-type=\"optional\" name=\"msg2_pre\" type=\"text\" placeholder=\"Hey\"></div><div class=\"form-group\"><label class=\"message-label\">Text after friend names (optional)</label><input class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\"                           data-type=\"optional\" name=\"msg2_post\" type=\"text\" placeholder=\"-- this is another suggested message!\"></div><div class=\"form-group\"><label class=\"input-label\">Facebook Post Image URL</label><input class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\" name=\"og_image\" type=\"text\" placeholder=\"https://your.org/image.jpg\"><span class=\"glyphicon glyphicon-remove form-control-feedback hide\"></span></div><div class=\"form-group\"><label class=\"input-label\">Facebook Post Title</label><input class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\" name=\"og_title\" type=\"text\" placeholder=\"Your post title.\"><span class=\"glyphicon glyphicon-remove form-control-feedback hide\"></span></div><div class=\"form-group\"><label class=\"input-label\">Facebook Post Description</label><textarea class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\"                              name=\"og_description\" type=\"text\"                              placeholder=\"Use this space to insert a brief description of the content that you want your target audience to click on\"></textarea><span class=\"glyphicon glyphicon-remove form-control-feedback hide\"></span></div><div class=\"form-group\"><label class=\"input-label\">Content URL</label><input class=\"form-control\" autocomplete=\"off\" data-js=\"formInput\" name=\"content_url\" type=\"text\" placeholder=\"http://your.org/content.html\"><span class=\"glyphicon glyphicon-remove form-control-feedback hide\"></span></div><div class=\"nav-button-container clearfix\"><button type=\"button\" class=\"btn pull-right\" data-js=\"createCampaignBtn\">Save Campaign</button><button type=\"button\" class=\"btn pull-right back-btn\" data-js=\"prevStep\">Go Back</button></div></div><div class=\"col-sm-7\"><div data-js=\"imageContainer\" class=\"image-container\"><img data-js=\"companionImage\" src=\"";
  if (helper = helpers.fbObjExampleURL) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.fbObjExampleURL); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\"></div></div><div data-js=\"popoverEl\" class=\"popover-target\"></div></div></div></section>";
  return buffer;
  })

});