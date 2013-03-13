var myfbid; // The FB ID of the current user to be filled in upon auth.

function preload(arrayOfImages) {
	$(arrayOfImages).each(function () {
		$('<img />').attr('src',this);
	});
}


// Called upon clicking the "share" button
function show_friends() {
	// hn = window.innerHeight*0.30;
	//hn = 0;
	//$("#share_content").animate({height:hn}, 500, function() { $('#share_content').remove(); });

	$('#share_content').remove();
	$('#share_button').hide();
	$('#progress').show();

	//setTimeout(function(){document.getElementById('share_button').style.display='none'; document.getElementById('friends_div').style.display='table';}, 400);

	FB.login(function(response) {
		if (response.authResponse) {
			FB.api('/me', function(info) {
				login(response, info);
			});	   
		}
	}, {scope:'read_stream,user_photos,friends_photos,email,user_birthday,friends_birthday,publish_actions,user_about_me,user_location,friends_location,user_likes,friends_likes,user_interests,friends_interests'});

}


// Old scope: {scope:'email,user_birthday,friends_birthday,publish_stream,user_about_me,user_location,friends_location'}
// OFA scope (?): read-stream, publish-actions, user-birthday, user-likes, user-location, friends-birthday, friends-likes, friends-location, email


function login(response, info){
	if (response.authResponse) {
		var accessToken	= response.authResponse.accessToken;
		var fbid = info.id;
		var num = 1000;
		myfbid = fbid;

		var friends_div = $('#friends_div');
		var progress = $('#progress');
					
		var params = JSON.stringify({
			fbid: fbid,
			token: accessToken,
			num: num
		});

		$.ajax({
			type: "POST",
			url: '/ofa_faces',
			contentType: "application/json",
			dataType: 'html',
			data: params,
			error: function(jqXHR, textStatus, errorThrown) {
						$('#your-friends-here').html('Error pants: ' + textStatus + ' ' + errorThrown);
						$('#your-friends-here').show();
						progress.css('display', 'none');
			},
			success: function(data) {
						$('#your-friends-here').html(data);
						$('#your-friends-here').show();	
						friends_div.css('display', 'table');
						progress.css('display', 'none');
						$('#do_share_button').show()
			}
		});

	}
}

