define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, functionType="function", escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = "", stack1, helper;
  buffer += "                <div data-js=\"campaignRow\" data-id=\"";
  if (helper = helpers.pk) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.pk); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\" class=\"row campaign-row\"><div class=\"col-sm-5\"><div data-id=\"";
  if (helper = helpers.pk) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.pk); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\" data-js=\"campaignName\" class=\"name\">";
  if (helper = helpers.name) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.name); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</div><div class=\"created\"><strong>Created </strong><span>on ";
  if (helper = helpers.create_dt) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.create_dt); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</span></div></div><div class=\"col-sm-4\">                    ";
  stack1 = helpers['if'].call(depth0, (depth0 && depth0.stats), {hash:{},inverse:self.noop,fn:self.program(2, program2, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "                    </div><div class=\"col-sm-3\"><!--Punting on this for now                        ";
  stack1 = helpers['if'].call(depth0, (depth0 && depth0.isPublished), {hash:{},inverse:self.program(6, program6, data),fn:self.program(4, program4, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "                        --><!--Use this when there are more options                        <div class=\"btn-group pull-right\"><button type=\"button\" class=\"btn btn-default\">Action</button><button type=\"button\" class=\"btn btn-default dropdown-toggle\" data-toggle=\"dropdown\"><span class=\"caret\"></span><span class=\"sr-only\">Toggle Dropdown</span></button><ul class=\"dropdown-menu\" role=\"menu\"><li><a href=\"#\">Edit</a></li><li><a href=\"#\">Clone</a></li><li><a href=\"#\">Reports</a></li><li><a href=\"#\">Faces Page</a></li><li><a href=\"#\">Facebook Post</a></li></ul></div>                        --></div></div>            ";
  return buffer;
  }
function program2(depth0,data) {
  
  
  return "                    ";
  }

function program4(depth0,data) {
  
  
  return "                            <div class=\"published pull-right\">Published</div>                        ";
  }

function program6(depth0,data) {
  
  
  return "                            <button data-js=\"editButton\" type=\"button\" class=\"btn btn-default pull-right editBtn\">Edit</button>                        ";
  }

  buffer += "<section class=\"col-sm-10 client-campaigns\"><div class=\"row\"><div class=\"col-sm-9\"><h1 class=\"heading\">Campaigns</h1></div><div class=\"col-sm-3\"><button data-js=\"createCampaignBtn\" type=\"button\" class=\"btn create-campaign-btn\">Create Campaign</button></div></div><div class=\"row\"><div class=\"col-sm-12\">            ";
  stack1 = helpers.each.call(depth0, (depth0 && depth0.campaigns), {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "        </div></div></section>";
  return buffer;
  })

});
