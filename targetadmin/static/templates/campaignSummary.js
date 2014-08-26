define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, functionType="function", escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "            <div class=\"group\"><div class=\"name\">Audience "
    + escapeExpression(((stack1 = (data == null || data === false ? data : data.index)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div>                ";
  stack1 = helpers.each.call(depth0, depth0, {hash:{},inverse:self.noop,fn:self.program(2, program2, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "            </div>        ";
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "                    ";
  stack1 = helpers.each.call(depth0, depth0, {hash:{},inverse:self.noop,fn:self.program(3, program3, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "                ";
  return buffer;
  }
function program3(depth0,data) {
  
  var buffer = "", stack1, helper;
  buffer += "                        <div class=\"value\">";
  if (helper = helpers.operator) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.operator); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + " ";
  if (helper = helpers.feature) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.feature); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + " ";
  if (helper = helpers.value) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.value); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</div>                    ";
  return buffer;
  }

  buffer += "<section class=\"col-sm-10 campaign-summary\"><div class=\"row divided\"><div class=\"col-sm-9\"><h1 class=\"heading\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</h1></div><div class=\"col-sm-3\"><button data-js=\"createCampaignBtn\" type=\"button\" class=\"btn create-campaign-btn\">Create Campaign</button></div></div><div class=\"row\"><div class=\"group\"><div class=\"name\">Campaign Name</div><div class=\"value\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div></div>        ";
  stack1 = helpers.each.call(depth0, ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.filters), {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "        <div class=\"group\"><div class=\"name\">Friend Suggestion Page</div><div class=\"value\">Headline: </div><div class=\"value\">Sub-header: </div><div class=\"value\">Thanks URL: <a href=\""
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.thanks_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.thanks_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</a></div><div class=\"value\">Error URL: <a href=\""
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.error_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.error_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</a></div></div><div class=\"group\"><div class=\"name\">Facebook Post</div><div class=\"value\">Cause or Organization: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.og_type)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div></div><div class=\"group\"><div class=\"value\">Suggested Message 1: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.suggested_message_1)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div><div class=\"value\">Suggested Message 2: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.suggested_message_2)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div></div><div class=\"group\"><div class=\"value\">Post Image: <img src=\""
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.og_image)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\"></div><div class=\"value\">Post Title: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.og_title)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div><div class=\"value\">Post Text: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.og_text)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div><div class=\"value\">Post Content URL: <a href=\""
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.content_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.content_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</a></div></div></div></section>";
  return buffer;
  })

});