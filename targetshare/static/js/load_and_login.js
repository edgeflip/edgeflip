/* only used if a non-authed user hits the faces page - /faces_frame endpoint 

this should probably redirect to a default page on client site
or show user a button (same behavior)

*/

var myfbid; // The FB ID of the current user to be filled in upon auth.
var debug_mode;

/* loads a bunch of images
*/
function preload(arrayOfImages) {
    $(arrayOfImages).each(function () {
        $('<img />').attr('src',this);
    });
}


/* pops up facebook's signin page in a _top window */
function doFBLogin() {

    // Should never get here since we should only send someone to the faces page upon authorizing...
    // Still, worth noting this will generate a pop-up without a click. Maybe we'd rather just give them
    // a button to click on instead?
    FB.login(function(response) {
        if (response.status != 'connected') {
            $('#your-friends-here').html(
                '<p id="reconnect_text">Please authorize the application in order to proceed.</p><div id="reconnect_button" class="button_big button_active" onclick="doFBLogin();">Connect</div>'
            );
            $('#progress').hide();
            $('#friends_div').css('display', 'table');
            $.ajax({
                type: "POST",
                url: "/record_event/",
                data: {
                    userid: myfbid,
                    appid: appid,
                    friends: [],
                    eventType: "auth_fail",
                    campaignid: campaignid,
                    contentid: contentid,
                    content: '',
                    token: tok
                }
            });
            $('#reconnect_button').click(function(){
                $('#progress').show();
                $('#reconnect_button').hide();
                $('#reconnect_text').hide();
            });
        }
    }, {scope:'read_stream,user_photos,friends_photos,email,user_birthday,friends_birthday,publish_actions,user_about_me,user_location,friends_location,user_likes,friends_likes,user_interests,friends_interests'});

}

var pollingTimer;
var pollingCount = 0;
/* AJAX call to hit /faces endpoint - receives HTML snippet & stuffs in DOM */
function login(fbid, accessToken, response, px3_task_id, px4_task_id, last_call){
    if (response.authResponse) {
        var num = 9;
        myfbid = fbid; // set the global variable for use elsewhere

        var friends_div = $('#friends_div');
        var progress = $('#progress');
        var your_friends_div = $('#your-friends-here');

        // In test mode, just use the provided test fbid & token for getting faces
        // Note, however, that you're logged into facebook as you, so trying to
        // share with someone else's friends is going to cause you trouble!
        var ajax_fbid = fbid;
        var ajax_token = accessToken;
        if (test_mode) {
            console.log('in test mode');
            console.log(test_token);
            ajax_fbid = test_fbid;
            ajax_token = test_token;
        }

        var params = {
            fbid: ajax_fbid,
            token: ajax_token,
            num: num,
            campaignid: campaignid,
            contentid: contentid,
            px3_task_id: px3_task_id,
            px4_task_id: px4_task_id,
            last_call: last_call
        };
        if (Url.window.query.efobjsrc)
            params.efobjsrc = Url.window.query.efobjsrc;

        $.ajax({
            type: "POST",
            url: '/faces/',
            dataType: 'json',
            data: params,
            error: function() {
                your_friends_div.show();
                progress.hide();
                clearTimeout(pollingTimer);
		top.location = errorURL; // set in frame_faces.html
            },
            success: function(data, textStatus, jqXHR) {
                campaignid = data.campaignid;
                contentid = data.contentid;
                if (data.status === 'waiting') {
                    if (pollingTimer) {
                        if (pollingCount > 40) {
                            clearTimeout(pollingTimer);
                            login(fbid, accessToken, response, data.px3_task_id, data.px4_task_id, true);
                        } else {
                            pollingCount += 1;
                            pollingTimer = setTimeout(function() {
                                login(fbid, accessToken, response, data.px3_task_id, data.px4_task_id)
                            }, 500);
                        }
                    } else {
                        pollingTimer = setTimeout(function() {
                            login(fbid, accessToken, response, data.px3_task_id, data.px4_task_id)
                        }, 500);
                    }
                } else {
                    displayFriendDiv(data.html, jqXHR);
                    clearTimeout(pollingTimer);
                    if (debug_mode){
                        recordEvent('faces_page_rendered');
                    }
                }
            }
        });

    }
}

function displayFriendDiv(data, jqXHR) {
    $('#your-friends-here').html(data);
    $('#your-friends-here').show();
    $('#friends_div').css('display', 'table');
    $('#progress').hide();
    $('#do_share_button').show()
}

var heartbeat_count = 0;
function heartbeat(){
    if (heartbeat_count <= 60) {
        recordEvent('heartbeat');
        heartbeat_count += 1;
        setTimeout(heartbeat, 1000);
    }
}
