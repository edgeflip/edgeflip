var myfbid; // The FB ID of the current user to be filled in upon auth.

function preload(arrayOfImages) {
	$(arrayOfImages).each(function () {
		$('<img />').attr('src',this);
	});
}


// Called upon clicking the "share" button
function show_friends() {
	hn = window.innerHeight*0.30;
	$("#share_content").animate({height:hn}, 500);

	setTimeout(function(){document.getElementById('share_button').style.display='none'; document.getElementById('friends_div').style.display='block';}, 400);

	FB.login(function(response) {
		if (response.authResponse) {
			FB.api('/me', function(info) {
				login(response, info);
			});	   
		}
	}, {scope:'email,user_birthday,status_update,publish_stream,user_about_me'});

}


function login(response, info){
	if (response.authResponse) {
		var accessToken	= response.authResponse.accessToken;
		var fbid = info.id;
		var num = 1000;
		myfbid = fbid;

		var friends_div = $('#your-friends-here');
		var progress = $('#progress');


		progress.show();	
					
		var params = JSON.stringify({
			fbid: fbid,
			token: accessToken,
			num: num
		});

		$.ajax({
			type: "POST",
			url: '/edgeflip_faces',
			contentType: "application/json",
			dataType: 'html',
			data: params,
			error: function(jqXHR, textStatus, errorThrown) {
						friends_div.text('Error pants: ' + textStatus + ' ' + errorThrown);
						progress.css('display', 'none');
			},
			success: function(data) {
						friends_div.html(data);	
						friends_div.show();
						progress.css('display', 'none');
						$('#do_share_button').show()
			}
		});

	}
}

