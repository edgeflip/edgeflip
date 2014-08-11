define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression;


  buffer += "<section id=\"login-container\" class=\"col-sm-10\"><h1 class=\"heading\">Login</h1><hr class=\"heading-separator\"><div class=\"row\"><div class=\"col-sm-3\"><form method=\"post\" class=\"form-horizontal\" role=\"form\" action=\"";
  if (helper = helpers.action) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.action); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\">                ";
  if (helper = helpers.token) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.token); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "                <div class=\"form-group\" data-js=\"inputContainer\"><label class=\"sr-only\" for=\"id_username\">Username</label><input type=\"text\" name=\"username\" class=\"form-control\" id=\"id_username\" placeholder=\"Username\"><span data-js=\"errorFeedback\" class=\"hide glyphicon glyphicon-remove form-control-feedback\"></span></div><div class=\"form-group\" data-js=\"inputContainer\"><label class=\"sr-only\" for=\"id_password\">Password</label><input type=\"password\" name=\"password\" class=\"form-control\" id=\"id_password\" placeholder=\"Password\"><span data-js=\"errorFeedback\" class=\"hide glyphicon glyphicon-remove form-control-feedback\"></span></div><div class=\"form-group\"><button type=\"submit\" class=\"btn\">Enter</button></div><input type=\"hidden\" name=\"next\" value=\"";
  if (helper = helpers.next) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.next); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\" /></form></div></div></section>";
  return buffer;
  })

});