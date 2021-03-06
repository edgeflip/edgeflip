define(['vendor/handlebars'], function(Handlebars) {

return Handlebars.template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression;


  buffer += "<section class=\"row campaign-wizard-intro\"><div class=\"col-sm-12\"><h1 class=\"heading\">Create A Targeted Sharing Campaign</h1><hr class=\"heading-separator\"><div class=\"row subheader\"><div class=\"col-sm-8\"><span>A targeted sharing campaign turns your supporters into influencers by asking them to share your content with friends who are likely to support your organization. </span><a href=\"";
  if (helper = helpers.howItWorksURL) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.howItWorksURL); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\" target=\"_blank\"> Learn More.</a></div><div class=\"col-sm-4\"><button data-js=\"getStartedBtn\" type=\"button\" class=\"btn\">Let's get started</button></div></div><div class=\"row\"><div class=\"col-sm-4\"><ul class=\"clearfix step-box filters-box\"><li><div class=\"table-wrap\"><span>Age 40 and Younger</span></div></li><li><div class=\"table-wrap\"><span>Lives in Chicago, Illinois, USA</span></div></li><li><div class=\"table-wrap\"><span>Female</span></div></li><li><div class=\"table-wrap\"><span>Age 20 and Older</span></div></li><li><div class=\"table-wrap\"><span>Topic: Healthcare</span></div></li><li><div class=\"table-wrap\"><span>Topic: Cycling</span></div></li></ul><div><div class=\"title\">Audience Targeting</div><div class=\"copy\">First, you'll select the target audience for your campaign by choosing a set of filters.</div></div></div><div class=\"col-sm-4\"><ul class=\"clearfix step-box friends-box\"><li><div class=\"xout\">x</div><div class=\"friend-image\"><img src=\"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xaf1/v/t1.0-1/c6.6.74.74/p86x86/247255_10150195668418865_3994903_n.jpg?oh=ff052b3c4d6ad1d682e5570fffb1328c&oe=5476EA62&__gda__=1415435304_8ddae63f6f625c1f8234c4fb5d37fc3f\"></div><div class=\"friend-text\"><div>Al</div><div>Gore</div></div></li><li><div class=\"xout\">x</div><div class=\"friend-image\"><img src=\"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p74x74/1620880_648232331904622_1905051898_n.jpg\"></div><div class=\"friend-text\"><div>Miss</div><div>Piggy</div></div></li><li><div class=\"xout\">x</div><div class=\"friend-image\"><img src=\"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xpf1/t1.0-1/c0.0.74.74/p74x74/10425368_10152547542152318_2027453845208090836_n.jpg\"></div><div class=\"friend-text\"><div>Ozzy</div><div>Osbourne</div></div></li></ul><div><div class=\"title\">Engage Your Supporters' Social Network</div><div class=\"copy\">Then, you'll configure the \"Friend Suggestion Page\" your supporters will use to share your campaign with their friends.</div></div></div><div class=\"col-sm-4\"><div class=\"step-box facebook-post-box\"><img src=\"";
  if (helper = helpers.facebookPostImage) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.facebookPostImage); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\"></div><div><div class=\"title\">Facebook Post</div><div>Finally, you'll create the Facebook post that your target audience will see. Clicking on this post will send users to your campaign content.</div></div></div></div></div></section>";
  return buffer;
  })

});