/* only used if a non-authed user hits the faces page - /faces_frame endpoint 

this should probably redirect to a default page on client site
or show user a button (same behavior)

*/

var debug_mode;

/* loads a bunch of images
*/
function preload(arrayOfImages) {
    $(arrayOfImages).each(function () {
        $('<img />').attr('src',this);
    });
}

function authFailure() {
    $('#your-friends-here').html(
        '<p id="reconnect_text">Please authorize the application in order to proceed.</p><div id="reconnect_button" class="button_big button_active" onclick="user.login();">Connect</div>'
    );
    $('#progress').hide();
    $('#friends_div').css('display', 'table');
    recordEvent('auth_fail');
    $('#reconnect_button').click(function(){
        $('#progress').show();
        $('#reconnect_button').hide();
        $('#reconnect_text').hide();
    });
}

var pollingTimer;
var pollingCount = 0;
/* AJAX call to hit /faces endpoint - receives HTML snippet & stuffs in DOM */
function login(fbid, accessToken, response, px3_task_id, px4_task_id, last_call){
    if (response.authResponse) {
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
            num_face: num_face,
            campaign: campaignid,
            content: contentid,
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
