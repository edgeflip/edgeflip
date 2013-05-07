/* only used if a non-authed user hits the faces page - /faces_frame endpoint 

this should probably redirect to a default page on client site
or show user a button (same behavior)

*/

var myfbid; // The FB ID of the current user to be filled in upon auth.

/* loads a bunch of images

XXX maybe unused
*/
function preload(arrayOfImages) {
	$(arrayOfImages).each(function () {
		$('<img />').attr('src',this);
	});
}


/* XXX I can die!*/
// Should no longer need this since we're subscribing to the statusChange event in FB.init()...

// function show_friends() {

// //	$('#share_content').remove();
// //	$('#share_button').hide();
// //	$('#progress').show();

// 	FB.getLoginStatus(function(response) {
// 	  if (response.status === 'connected') {
// 	    var uid = response.authResponse.userID;
// 	    var tok = response.authResponse.accessToken;
// 	    login(uid, tok, response);
// 	  } else {
// 	  	// User isn't logged in or hasn't authed, so try doing the login directly
// 	    // (note: if we wanted to detect logged in to FB but not authed, could use status==='not_authorized')
// 	    doFBLogin();
// 	  }
// 	});

// }

/* pops up facebook's signin page in a _top window */
function doFBLogin() {

	// Should never get here since we should only send someone to the faces page upon authorizing...
	// Still, worth noting this will generate a pop-up without a click. Maybe we'd rather just give them
	// a button to click on instead?
	FB.login(function(response) {
		if (response.authResponse) {
			// Not sure we need this call -- can't we just grab the id from the response, too?
			FB.api('/me', function(info) {
				login(info.id, response.authResponse.accessToken, response);
			});
		} else {
			// zzz Figure out what to actually do here!
			alert("Rocco, sit on the other side. You block the rearview mirror.");
		}
	}, {scope:'read_stream,user_photos,friends_photos,email,user_birthday,friends_birthday,publish_actions,user_about_me,user_location,friends_location,user_likes,friends_likes,user_interests,friends_interests'});

}

/* AJAX call to hit /faces endpoint - receives HTML snippet & stuffs in DOM */
function login(fbid, accessToken, response){
	if (response.authResponse) {
		var num = 6;
		myfbid = fbid; // set the global variable for use elsewhere

		var friends_div = $('#friends_div');
		var progress = $('#progress');
		var your_friends_div = $('#your-friends-here');

		var params = JSON.stringify({
			fbid: fbid,
			token: accessToken,
			num: num,
			sessionid: sessionid,	// global session id was pulled in from query string above
			campaignid: campaignid,
			contentid: contentid
		});

		$.ajax({
			type: "POST",
			url: '/faces',
			contentType: "application/json",
			dataType: 'html',
			data: params,
			error: function(jqXHR, textStatus, errorThrown) {
				your_friends_div.html('Error pants: ' + textStatus + ' ' + errorThrown);
				your_friends_div.show();
				progress.hide();
			},
			success: function(data, textStatus, jqXHR) {
				your_friends_div.html(data);
				your_friends_div.show();	
				friends_div.css('display', 'table');
				progress.hide();
				$('#do_share_button').show()

				var header_efsid = jqXHR.getResponseHeader('X-EF-SessionID');
				sessionid = header_efsid || sessionid;
			}
		});

	}
}

