define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, functionType="function", escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = "", stack1, helper;
  buffer += "\n                <div data-js=\"campaignRow\" data-id=\"";
  if (helper = helpers.pk) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.pk); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\" class=\"row campaign-row\">\n                    <div class=\"col-sm-5\">\n                        <div data-id=\"";
  if (helper = helpers.pk) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.pk); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\" data-js=\"campaignName\" class=\"name\">";
  if (helper = helpers.name) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.name); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</div>\n                        <div class=\"created\">\n                            <strong>Created</strong>\n                            <span>on ";
  if (helper = helpers.create_dt) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.create_dt); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</span>\n                        </div>\n                    </div>\n                    <div class=\"col-sm-4\">\n                    ";
  stack1 = helpers['if'].call(depth0, (depth0 && depth0.stats), {hash:{},inverse:self.noop,fn:self.program(2, program2, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n                    </div>\n                    <div class=\"col-sm-3\">\n                        ";
  stack1 = helpers['if'].call(depth0, (depth0 && depth0.isPublished), {hash:{},inverse:self.program(6, program6, data),fn:self.program(4, program4, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n                        <!--Use this when there are more options\n                        <div class=\"btn-group pull-right\">\n                            <button type=\"button\" class=\"btn btn-default\">Action</button>\n                            <button type=\"button\" class=\"btn btn-default dropdown-toggle\" data-toggle=\"dropdown\">\n                                <span class=\"caret\"></span>\n                                <span class=\"sr-only\">Toggle Dropdown</span>\n                            </button>\n                            <ul class=\"dropdown-menu\" role=\"menu\">\n                                <li><a href=\"#\">Edit</a></li>\n                                <li><a href=\"#\">Clone</a></li>\n                                <li><a href=\"#\">Reports</a></li>\n                                <li><a href=\"#\">Faces Page</a></li>\n                                <li><a href=\"#\">Facebook Post</a></li>\n                            </ul>\n                        </div>\n                        -->\n                    </div>\n                </div>\n            ";
  return buffer;
  }
function program2(depth0,data) {
  
  
  return "\n                    ";
  }

function program4(depth0,data) {
  
  
  return "\n                            <div class=\"published pull-right\">Published</div>\n                        ";
  }

function program6(depth0,data) {
  
  
  return "\n                            <button data-js=\"editButton\" type=\"button\" class=\"btn btn-default pull-right\">Edit</button>\n                        ";
  }

  buffer += "<section class=\"col-sm-10 client-home\">\n    <div class=\"row header\">\n        <div class=\"col-sm-9\">\n            <h1>Campaigns</h1>\n        </div>\n        <div class=\"col-sm-3\">\n            <button data-js=\"createCampaignBtn\" type=\"button\" class=\"btn create-campaign-btn\">Create Campaign</button>\n        </div>\n    </div>\n    <div class=\"row\">\n        <div class=\"col-sm-12\">\n            ";
  stack1 = helpers.each.call(depth0, (depth0 && depth0.campaigns), {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n        </div>\n    </div>\n</section>\n\n\n";
  return buffer;
  })

});