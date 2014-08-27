define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, functionType="function", escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  
  return "    ";
  }

function program3(depth0,data) {
  
  
  return "        <div class=\"row\"><div class=\"group\">            Nice job! You've successfully created a Targeted Sharing campaign. Here's your campaign summary—please make sure everything looks right before you hit \"Publish Now.\"        </div></div>    ";
  }

function program5(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "            <div class=\"group\">                ";
  stack1 = helpers['if'].call(depth0, (data == null || data === false ? data : data.index), {hash:{},inverse:self.program(8, program8, data),fn:self.program(6, program6, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "                ";
  stack1 = helpers.each.call(depth0, depth0, {hash:{},inverse:self.noop,fn:self.program(10, program10, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "            </div>        ";
  return buffer;
  }
function program6(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "                    <div class=\"name\">Fallback Audience "
    + escapeExpression(((stack1 = (data == null || data === false ? data : data.index)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div>                ";
  return buffer;
  }

function program8(depth0,data) {
  
  
  return "                    <div class=\"name\">Target Audience</div>                ";
  }

function program10(depth0,data) {
  
  var buffer = "";
  buffer += "                    <div class=\"value\">"
    + escapeExpression((typeof depth0 === functionType ? depth0.apply(depth0) : depth0))
    + "</div>                ";
  return buffer;
  }

function program12(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "            <div class=\"group\"><span class=\"name\">Empty Fallback: </span>            ";
  stack1 = helpers['if'].call(depth0, ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.empty_fallback), {hash:{},inverse:self.program(15, program15, data),fn:self.program(13, program13, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "            </div>        ";
  return buffer;
  }
function program13(depth0,data) {
  
  
  return "                Yes            ";
  }

function program15(depth0,data) {
  
  
  return "                No            ";
  }

function program17(depth0,data) {
  
  
  return "        ";
  }

function program19(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "            <div class=\"group\"><div><span class=\"name\">Campaign Test URL: </span> "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.live_snippet_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div>                All your changes have been saved. If you're not ready to publish your campaign now, you can always come back later and pick up where you left off.            </div>        ";
  return buffer;
  }

  buffer += "<section class=\"col-sm-10 campaign-summary\"><div class=\"row divided\"><div class=\"col-sm-9\"><h1 class=\"heading\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</h1></div><div class=\"col-sm-3\"><button data-js=\"createCampaignBtn\" type=\"button\" class=\"btn create-campaign-btn\">Create Campaign</button></div></div>    ";
  stack1 = helpers['if'].call(depth0, ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.is_published), {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "    <div class=\"row\"><div class=\"group\"><div class=\"name\">Campaign Name</div><div class=\"value\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div></div>        ";
  stack1 = helpers.each.call(depth0, ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.cleaned_filters), {hash:{},inverse:self.noop,fn:self.program(5, program5, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "        ";
  stack1 = helpers['if'].call(depth0, ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.cleaned_filters), {hash:{},inverse:self.noop,fn:self.program(12, program12, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "        <div class=\"group\"><div class=\"name\">Friend Suggestion Page</div><div class=\"value\">Headline: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.headline)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div><div class=\"value\">Sub-header: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.subheader)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div><div class=\"value\">Thanks URL: <a href=\""
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
    + "</a></div></div>        ";
  stack1 = helpers['if'].call(depth0, ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.is_published), {hash:{},inverse:self.program(19, program19, data),fn:self.program(17, program17, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "    </div></section>";
  return buffer;
  })

});