define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, functionType="function", escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "            <div class=\"group\"><div class=\"value\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.message)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div></div>        ";
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "            <div class=\"group\">                ";
  stack1 = helpers['if'].call(depth0, (data == null || data === false ? data : data.index), {hash:{},inverse:self.program(6, program6, data),fn:self.program(4, program4, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "                ";
  stack1 = helpers.each.call(depth0, depth0, {hash:{},inverse:self.noop,fn:self.program(8, program8, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "            </div>        ";
  return buffer;
  }
function program4(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "                    <div class=\"name\">Fallback Audience "
    + escapeExpression(((stack1 = (data == null || data === false ? data : data.index)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div>                ";
  return buffer;
  }

function program6(depth0,data) {
  
  
  return "                    <div class=\"name\">Target Audience</div>                ";
  }

function program8(depth0,data) {
  
  var buffer = "";
  buffer += "                    <div class=\"value\">"
    + escapeExpression((typeof depth0 === functionType ? depth0.apply(depth0) : depth0))
    + "</div>                ";
  return buffer;
  }

function program10(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "            <div class=\"group\"><span class=\"name\">Empty Fallback: </span>            ";
  stack1 = helpers['if'].call(depth0, ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.empty_fallback), {hash:{},inverse:self.program(13, program13, data),fn:self.program(11, program11, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "            </div>        ";
  return buffer;
  }
function program11(depth0,data) {
  
  
  return "                Yes            ";
  }

function program13(depth0,data) {
  
  
  return "                No            ";
  }

function program15(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "            <div class=\"group\"><div class=\"name\">Campaign URL</div><div class=\"value\"><a href=\""
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.sharing_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\" target=\"_blank\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.sharing_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</a></div></div>        ";
  return buffer;
  }

  buffer += "<section class=\"col-sm-10 campaign-summary\"><div class=\"row divided\"><div class=\"col-sm-9\"><h1 class=\"heading\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</h1></div></div><div class=\"row\">        ";
  stack1 = helpers['if'].call(depth0, ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.message), {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "        <div class=\"group\"><div class=\"name\">Campaign Name</div><div class=\"value\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div></div>        ";
  stack1 = helpers.each.call(depth0, ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.cleaned_filters), {hash:{},inverse:self.noop,fn:self.program(3, program3, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "        ";
  stack1 = helpers['if'].call(depth0, ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.cleaned_filters), {hash:{},inverse:self.noop,fn:self.program(10, program10, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "        <div class=\"group\"><div class=\"name\">Friend Suggestion Page</div><div class=\"value\">Headline: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.headline)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div><div class=\"value\">Sub-header: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.subheader)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div><div class=\"value\">Thanks URL: <a href=\""
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.thanks_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\" target=\"_blank\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.thanks_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</a></div><div class=\"value\">Error URL: <a href=\""
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.error_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\" target=\"_blank\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.error_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</a></div></div><div class=\"group\"><div class=\"name\">Facebook Post</div><div class=\"value\">Cause or Organization: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.org_name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div></div><div class=\"group\"><div class=\"value\">Suggested Message 1: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.suggested_message_1)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div><div class=\"value\">Suggested Message 2: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.suggested_message_2)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div></div><div class=\"group\"><div class=\"value\">Post Image URL: <a href=\""
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.og_image)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\" target=\"_blank\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.og_image)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</a></div><div class=\"value\">Post Title: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.og_title)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div><div class=\"value\">Post Text: "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.og_description)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</div><div class=\"value\">Post Content URL: <a href=\""
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.content_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\" target=\"_blank\">"
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.content_url)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "</a></div></div>        ";
  stack1 = helpers['if'].call(depth0, ((stack1 = (depth0 && depth0.campaign)),stack1 == null || stack1 === false ? stack1 : stack1.sharing_url), {hash:{},inverse:self.noop,fn:self.program(15, program15, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "        <div class=\"group\"><button data-js=\"homeBtn\" type=\"button\" class=\"btn\">Home</button></div></div></section>";
  return buffer;
  })

});