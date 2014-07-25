/* ALL TEH CODES */

edgeflip.FB_APP_ID = '{{ fb_params.fb_app_id }}';
edgeflip.FB_APP_NAME = '{{ fb_params.fb_app_name }}';
edgeflip.FB_ACTION_TYPE = '{{ fb_params.fb_action_type }}';
edgeflip.FB_OBJ_TYPE = '{{ fb_params.fb_object_type }}';
edgeflip.FB_OBJ_URL = '{{ fb_params.fb_object_url | safe }}';

RECIPS_LIST_CONTAINER = "recips_list";

// all the friend data here
var friendFromFbid = {
    {% for friend in all_friends %}
        {{friend.fbid}}: {"fbid": {{friend.fbid}}, "name": "{{friend.name}}", "fname": "{{friend.fname}}", "lname": "{{friend.lname}}"}{% if not forloop.last %},{% endif %}
    {% endfor %}
};

// on deck circle for friends who will get slotted in, we shift them off as we go
var faceFriends = [
    {% for friend in face_friends %}
        {{friend.fbid}},
    {% endfor %}
].slice({{ num_face }});

function getRecipElts() {
    return $('#message_form_editable .recipient');
}

function getRecipFbids() {
    var fbids = [];
    var recipElts = getRecipElts();
    for (var i=0; i<recipElts.length; i++) {
        var fbid = parseInt(recipElts[i].id.split('-')[1]);
        if(fbid) {
            fbids.push(fbid);
        }
    }
    return fbids;
}

function isRecip(fbid) {
    return (getRecipFbids().indexOf(fbid) > -1);
}

function htmlRecip(fbid) {
    var html = "<span class='recipient message_friend_name' id='recipient-"+fbid+"' contentEditable='False'>";
    html += friendFromFbid[fbid].name + "<span class='message_x' onClick='unselectFriend("+fbid+");'>x</span></span>&nbsp;";
    return html;
}

function htmlRecipsList() {
    var recipHtmls = [];
    getRecipElts().each(function() {
        var outerHtml = $(this).clone().wrap('<p>').parent().html();
        recipHtmls.push(outerHtml);
    });
    return commafy(recipHtmls);
}

function reformatRecipsList() {
    var recipsHtml = htmlRecipsList();
    $('#'+RECIPS_LIST_CONTAINER).empty().append(recipsHtml);
}

function htmlRecipAdded(fbid) {
  var name = friendFromFbid[fbid].name;
  var html = "<div class='added_friend' id='added-"+ fbid + "'>" + name;
  html += "<div class='added_x' onClick='removeFriend("+fbid+");'>x</div></div>";
  return html;
}

/* advances the active button (if current active is already ahead of index param, it does nothing) */
function activateButton(buttons, requestIdx) {
    var classOn = 'button_active';
    var classOff = 'button_inactive';

    var currentIdx = 0;
    for (var i=1; i<buttons.length; i++) {
        if (buttons[i].hasClass(classOn)) {
            currentIdx = i;
        }
    }
    var activateIdx = (currentIdx > requestIdx) ? currentIdx : requestIdx;
    for (var i=1; i<buttons.length; i++) {
        if (i == activateIdx) {
            buttons[i].removeClass(classOff).addClass(classOn);
        } else {
            buttons[i].removeClass(classOn).addClass(classOff);
        }
    }
    return activateIdx;
}
var buttons = [ null, $('#button_select_all'), $('#button_sugg_msg'), $('#button_do_share') ];

function activateSuggestButton() {
    return activateButton(buttons, 2);
}
function activateShareButton() {
    return activateButton(buttons, 3);
}

function commafy(things) {
    switch (things.length) {
        case 0:
            return "";
        case 1:
            return things[0];
        case 2:
            return things[0] + " and "+ things[1];
        default:
            var ret = "";
            for (var i=0; i < (things.length-1); i++) {
                ret += things[i] + ", ";
            }
            ret += " and " + things[things.length-1];
            return ret;
    }
}

function selectFriend() {
    /* Register & record friend(s) UI selection
     *
     * Examples:
     *
     *     selectFriend(fbid)
     *     selectFriend(fbid0, fbid1, fbid2)
     *     selectFriend.apply(this, fbids)
     *
     */
    var fbid, index, novelIds = [];
    for (index in arguments) {
        fbid = arguments[index];
        if (isRecip(fbid)) {
            continue;
        }

        // If we've used the suggest button, we should have a recips list container,
        // so stick it in there and reformat
        if ($('#' + RECIPS_LIST_CONTAINER).length > 0) {
            $('#' + RECIPS_LIST_CONTAINER).append(htmlRecip(fbid));
            reformatRecipsList();
        } else { // otherwise, insert at cursor
            insertRecipAtCursor(htmlRecip(fbid));
        }

        syncFriendBoxes();  // update the appearance of the friend box
        activateSuggestButton();  // advance the button highlight
        novelIds.push(fbid);
    }

    if (novelIds.length === 0)
        // we didn't do anything
        return false;

    if (edgeflip.faces.debug) {
        var selection_type = 'selected_friend';
        if (novelIds.length === 1 && document.getElementById('wrapper-' + novelIds[0]) === null) 
            selection_type = 'manually_selected_friend';
        edgeflip.events.record(selection_type, {friends: novelIds});
    }

    $("body").trigger('friendsSelected');

    return true;
}

/* runs when user deselects a friend 

activated by unclick a friend to share with or from manual drop or in edit message

*/
function unselectFriend(fbid) {
    if (isRecip(fbid)) {
        $('#recipient-'+fbid).remove();    // remove the friend from the message
        syncFriendBoxes();
        reformatRecipsList();
        if (edgeflip.faces.debug) {
            var unselection_type = 'unselected_friend';
            if (document.getElementById('wrapper-' + fbid) === null)
                unselection_type = 'manually_unselected_friend';

            edgeflip.events.record(unselection_type, {friends: [fbid]});
        }
        return true;
    } else {
        return false;
    }
}

function syncFriendBoxes() {
    // check the friend boxes upstairs first
    var friendBoxes = $('.friend_box');
    for (var i=0; i<friendBoxes.length; i++) {
        var fbid = parseInt(friendBoxes[i].id.split('-')[1]);
        if (isRecip(fbid)) {
            $('#friend-'+fbid).removeClass('friend_box_unselected').addClass('friend_box_selected');
            $('#wrapper-'+fbid+' .xout').hide();
          }
        else {
            $('#added-'+fbid).remove();                  // remove the manually added friend (if it exists)
            $('#friend-'+fbid).removeClass('friend_box_selected').addClass('friend_box_unselected');
            $('#wrapper-'+fbid+' .xout').show();
        }
    }

    // go through the manual add friends and make sure they should be there
    var friendBoxesAdded = $('.added_friend');
    for (var i=friendBoxesAdded.length-1; i>=0; i--) {
        var box = friendBoxesAdded[i]
        var fbid = parseInt(friendBoxesAdded[i].id.split('-')[1]);
        if (!isRecip(fbid)) {
            $(friendBoxesAdded[i]).remove();
        }
    }

    // finally, if there are any recips without a box, add a manual one
    var recipIds = getRecipFbids();
    for (var i=0; i<recipIds.length; i++) {
        var fbid = recipIds[i];
        if (($('#added-'+fbid).length == 0) && ($('#friend-'+fbid).length == 0)) {
              $('#picked_friends_container').append(htmlRecipAdded(fbid))
        }
    }
}

/* focuses & moves cursor to end of content-editable div */
// grabbed from stackoverflow:
// http://stackoverflow.com/questions/1125292/how-to-move-cursor-to-end-of-contenteditable-entity
function msgFocusEnd() {
    var contentEditableElement = document.getElementById('message_form_editable'),
        range,
        selection;
    
    $('#message_form_editable').focus();

    if(document.createRange)//Firefox, Chrome, Opera, Safari, IE 9+
    {
        range = document.createRange();//Create a range (a range is a like the selection but invisible)
        range.selectNodeContents(contentEditableElement);//Select the entire contents of the element with the range
        range.collapse(false);//collapse the range to the end point. false means collapse to end rather than the start
        selection = window.getSelection();//get the selection object (allows you to change selection)
        selection.removeAllRanges();//remove any selections already made
        selection.addRange(range);//make the range you have just created the visible selection
    }
    else if(document.selection)//IE 8 and lower
    { 
        range = document.body.createTextRange();//Create a range (a range is a like the selection but invisible)
        range.moveToElementText(contentEditableElement);//Select the entire contents of the element with the range
        range.collapse(false);//collapse the range to the end point. false means collapse to end rather than the start
        range.select();//Select the range (make it the visible selection
    }
}

/* if cursor in editable div, & user selects a friend, at add insertion point */
// Thank you stackoverflow!
// http://stackoverflow.com/questions/6690752/insert-html-at-cursor-in-a-contenteditable-div
function insertRecipAtCursor(html) {

    var sel, range;
    if ( elementContainsSelection($('#message_form_editable').get(0)) ) {
        if (window.getSelection) {
            // IE9 and non-IE
            sel = window.getSelection();
            if (sel.getRangeAt && sel.rangeCount) {
                range = sel.getRangeAt(0);
                range.deleteContents();

                // Range.createContextualFragment() would be useful here but is
                // non-standard and not supported in all browsers (IE9, for one)
                var el = document.createElement("div");
                el.innerHTML = html;
                var frag = document.createDocumentFragment(), node, lastNode;
                while ( (node = el.firstChild) ) {
                    lastNode = frag.appendChild(node);
                }
                range.insertNode(frag);

                // Preserve the selection
                if (lastNode) {
                    range = range.cloneRange();
                    range.setStartAfter(lastNode);
                    range.collapse(true);
                    sel.removeAllRanges();
                    sel.addRange(range);
                }
            }
        } else if (document.selection && document.selection.type != "Control") {
            // IE < 9
            document.selection.createRange().pasteHTML(html);
        }

    } else {
        $('#message_form_editable').append(html);
    }
}

// more stackoverflow:
// http://stackoverflow.com/questions/8339857/how-to-know-if-selected-text-is-inside-a-specific-div/8340432#8340432
function isOrContains(node, container) {
    while (node) {
        if (node === container) {
            return true;
        }
        node = node.parentNode;
    }
    return false;
}

function elementContainsSelection(el) {
    var sel;
    if (window.getSelection) {
        sel = window.getSelection();
        if (sel.rangeCount > 0) {
            for (var i=0; i<sel.rangeCount; ++i) {
                if (!isOrContains(sel.getRangeAt(i).commonAncestorContainer, el)) {
                    return false;
                }
            }
            return true;
        }
    } else if ( (sel = document.selection) && sel.type != "Control") {
        return isOrContains(sel.createRange().parentElement(), el);
    }
    return false;
}

/* populates message div w/ suggested text */
function useSuggested(msgs) {
    edgeflip.events.record('suggest_message_click');

    // grab the pre and post off the front of the queue and stick 'em back on the end
    var msgPair = msgs.shift(),
        msgPre = msgPair[0],
        msgPost = msgPair[1],
        msgNamesContHtml = "<span id='" + RECIPS_LIST_CONTAINER + "'></span>",
        recipsHtml;
    
    msgs.push(msgPair);

    // If they don't have anyone checked, using the suggested message adds everyone
    if (getRecipFbids().length == 0) {
        selectAll(true);
    }

    if( msgPre.charAt(msgPre.length - 1) !== '' ) {
        msgPre += ' ';
    }
    
    if( msgPost.charAt(0) !== '' ) {
        msgPost = ' ' + msgPost;
    }
        
    recipsHtml = htmlRecipsList();  // these are going to get blown away, so capture them now

    $('#message_form_editable').empty().append(msgPre, msgNamesContHtml, msgPost);
    $('#'+RECIPS_LIST_CONTAINER).append(recipsHtml);
   
    activateShareButton();

    //we don't want to mess with whatever the safari iOS is looking at
    //they could be at any number of zoom levels
    if( window.navigator.userAgent.match(/(iPad|iPhone)/i) ) {
    } else {
        var shareButton = $('#button_do_share', document);
            offset = shareButton.offset(),
            difference = ( offset.top + shareButton.outerHeight(true) ) -
                         ( $('html,body').scrollTop() + $(window).height() );

        //only scroll if share button is below the viewport
        if( difference > 0 ) {
            $('html,body',document).animate(
                { scrollTop: '+=' + difference },
                { duration: 1000 }
            );
        }
    }
}

/* selects all friends */
function selectAll(skipRecord) {
    // Have to filter for visible because a friend div might be hidden
    // while awaiting response of an ajax suppression call
    var fbid,
        fbids = [],
        unselected_friend_boxes = $(".friend_box:visible").not(".friend_box_selected"),
        count = getRecipFbids().length;

    if (!skipRecord) {
        edgeflip.events.record('select_all_click');
    }

    //we want to alert only if there are unselected friend boxes
    //and the count is already at max_face
    unselected_friend_boxes.each( function() {
        if(count === edgeflip.faces.max_face ) {
            alertTooMany();
            return false;
        }
        fbid = parseInt(this.id.split('-')[1]);
        if (!isRecip(fbid)) {
            count++;
            fbids.push(fbid);
        }
    } );

    $("body").one('friendsSelected', function() {
        //we don't want to mess with whatever the safari iOS is looking at
        //they could be at any number of zoom levels
        if( window.navigator.userAgent.match(/(iPad|iPhone)/i) ) {
        } else {
            $('html,body',document).animate(
                { scrollTop: $('#button_sugg_msg', document).offset().top - 30 },
                { duration: 1000 } );
        }
    } );

    if( fbids.length ) { selectFriend.apply(this, fbids); }
    activateSuggestButton();
}

/* Tell the user max_face have already been selected */
function alertTooMany() { alert("Sorry: only " + edgeflip.faces.max_face + " friends can be tagged."); }

// Toggle the recipient state of a friend upon checking or unchecking
function toggleFriend(fbid) {
    var count;

    if (isRecip(fbid)) {
          unselectFriend(fbid);
    } else if( getRecipFbids().length === edgeflip.faces.max_face ) {
        alertTooMany();
    } else {
        selectFriend(fbid);
    }
}

/* called when someone suppresses a friend (X in faces list) */
function doReplace(old_fbid) {
    var div_id = '#wrapper-'+old_fbid;

    // Remove the friend from the messages
    unselectFriend(old_fbid);

    // Hide the suppressed div immediately, because the response to
    // the ajax call can be a little sluggish...
    $(div_id).hide();

    if (faceFriends.length > 0) {
        // Note that we're HTML-unescaping the first and last name to send back
        // to the server for templating -- the template is going to escape these
        // and we don't want them getting escaped twice! Hockey & ugly, I know,
        // but this will work until we move to a smarter system of front-end
        // templating...
        var fbid = faceFriends.shift();
        var fname = $("<div/>").html(friendFromFbid[fbid].fname).text();
        var lname = $("<div/>").html(friendFromFbid[fbid].lname).text();

        // Update the friends shown
        friendHTML(old_fbid, fbid, fname, lname, div_id);

    } else {
        // No new friends to add, so just remove this one
        // (note that we have to remove rather than hide the element to avoid avoid accidentally
        // including the friend in the message that gets sent!)
        friendHTML(old_fbid, '', '', '', div_id);
        // $(div_id).remove();
    }

    return false;
}


// Ajax call to tell our server the friend has been suppressed and get the HTML for the next one
function friendHTML(oldid, id, fname, lname, div_id) {
    var new_html;
    $.ajax({
        type: "POST",
        url: '/suppress/',
        dataType: 'html',
        data: {
            userid: edgeflip.faces.user.fbid, // edgeflip.User constructed in frame_faces.html
            appid: edgeflip.FB_APP_ID,
            content: edgeflip.FB_APP_NAME + ':' + edgeflip.FB_OBJ_TYPE + ' ' + edgeflip.FB_OBJ_URL,
            oldid: oldid,
            newid: id,
            fname: fname,
            lname: lname,
            campaignid: edgeflip.faces.campaignid, // campaignid and contentid set in frame_faces.html
            contentid: edgeflip.faces.contentid
        },
        error: function(jqXHR, textStatus, errorThrown) {
            //new_html = 'Error pants: ' + textStatus + ' ' + errorThrown;
            //$(div_id).replaceWith(new_html);
            // Something went wrong, so just remove the div as though no friend was returned
            $(div_id).remove();
        },
        success: function(data, textStatus, jqXHR) {
            if (id) {
                new_html = data;
                $(div_id).replaceWith(new_html);
                $('#wrapper-' + id + ' .xout').click(
                    function(e) { e.stopImmediatePropagation(); doReplace( $(this).data('id') ); } );
            } else {
                // We hid it above, but still need to actually remove it if there's
                // no new friend coming in (otherwise, a select all will still add this friend...)
                $(div_id).remove();
            }
        }
    });
}

function sendShare() {
    helperTextDisappear();
    $('#friends_div').hide();
    $('#progress').show();
    $('#progress').removeClass('loading').addClass('sending');
    

    var progressBar = false,
        progress = 10,
        intervalId;

    if( $('#spinner').css('background-image') === 'none' ) {
        progressBar = true;
        updateProgressBar(progress);
        intervalId = setInterval(
            function() { progress += 10;
                         updateProgressBar(progress); },
            500 );
    }

    var recips = getRecipFbids();
    for (var i=0; i < recips.length; i++) {
        $('#recipient-'+recips[i]).replaceWith("@[" + recips[i] + "]"); // FB format for mention tags: @[fbid]
    }

    var recipsList = $('#message_form_editable .'+RECIPS_LIST_CONTAINER);
    if (recipsList.length > 0) {
        recipsList.replaceWith(recipsList.text());
    }

    var msg = "";
    msg = $('#message_form_editable').text();
    msg = msg.replace(/[\n\r]/g, ' ');
    msg = msg.substring(0, 1500); // Limit submissions to 1,500 characters (different from keydown to allow for possibility that fbid's are longer)

    // The actual call to do the sharing
    var paramObj = { message: msg }
    paramObj[edgeflip.FB_OBJ_TYPE] = edgeflip.FB_OBJ_URL; // gotta do it this way since the property name is dynamic
    FB.api(
        '/me/' + edgeflip.FB_APP_NAME + ':' + edgeflip.FB_ACTION_TYPE,
        'post',
        paramObj,
        function(response) {
            if (!response || response.error) {
                // show an alert and then redirect them to wherever the client wants them to go in this case...
                // console.log('Error occured ' + response.error.message)
                edgeflip.events.record('share_fail', {
                    errorMsg: response.error,
                    complete: function() {
                        alert("Sorry. An error occured sending your message to facebook. Please try again later.");
                        outgoingRedirect(edgeflip.faces.errorURL); // set in frame_faces.html
                    }
                });
            } else {
                // thank you page redirect happens in recordShare()
                if( progressBar ) {
                    clearInterval(intervalId);
                    if( progress < 70 ) { updateProgressBar(70); }
                }
                recordShare(response.id, msg, recips);
            }
        }
    );
}

/* hits facebook API */
// Called when someone actually shares a message
function doShare(recursive) {

    if (edgeflip.faces.test_mode) {
        alert("Sharing is not allowed in test mode!");
        return;
    }

    // Quick checks: has the user selected a message and at least one friend with whom to share?
    if (getRecipFbids().length == 0) {
        if (confirm("You haven't chosen any friends to share with.\n\nClick OK to share with all suggested friends or CANCEL to return to the page.")) {
            selectAll(true);
        } else {
            if (edgeflip.faces.debug) {
                edgeflip.events.record('empty_share');
            }
            return;
        }
    }
    if (!recursive)
        // In case the user is indecisive about publishing, let's only record
        // share_click once.
        edgeflip.events.record('share_click');

    FB.login(function(response) {
        // FB.login will tell you if a user is authorized but will not tell 
        // you which permissions they have granted us.
        var perm_check = $.ajax({
            url: 'https://graph.facebook.com/' + edgeflip.faces.user.fbid + '/permissions/',
            data: {access_token: edgeflip.faces.user.token}
        });
        perm_check.done(function(resp) {
            if (resp.data[0].publish_actions) {
                edgeflip.events.record('publish_accepted'); 
                sendShare();
            } else {
                edgeflip.events.record('publish_declined');
                if (confirm("Without permission to publish, we're unable to share this message with your friends. \n\nClick OK to grant permission, or CANCEL to leave the page")) {
                    edgeflip.events.record('publish_reminder_accepted');
                    doShare(true);
                } else {
                    edgeflip.events.record('publish_reminder_declined', {
                        complete: function() {
                            outgoingRedirect(edgeflip.faces.errorURL); // set in frame_faces.html
                        }
                    });
                }
            }
        });
        perm_check.fail(function(resp, textStatus) {
            edgeflip.events.record('publish_unknown', {
                content: textStatus,
                errorMsg: textStatus
            });
            sendShare();
        });
    }, {scope: "publish_actions"});
}


function recordShare(actionid, shareMsg, recips) {
    /* records share event on edgeflip servers; redirects user to thank you page */
    edgeflip.events.record('shared', {
        actionid: actionid,
        friends: recips,
        shareMsg: shareMsg,
        complete: function() {
            updateProgressBar(100);
            // thanksURL set in frame_faces.html
            setTimeout( function() { outgoingRedirect(edgeflip.faces.thanksURL); }, 500 );
        }
    });
}

function helperTextDisappear() {
    $('#message_helper_txt').remove();
}
/////////////////////////////////

// on load stuff

$(document).ready(function() {
    /* event binding & key handling for editable msg div*/

    var editable = $('#message_form_editable');
    var msg_length = $('#message_form_editable').text().length;
    var max_msg_length = 1000;

    // key presses that we'll let through in the event the message has gotten too long
    var allow_keys = [
                        8,  // Backspace
                        46, // Delete
                        20, // Caps Lock
                        91, // Command
                        93, // Right Command
                        17, // Control
                        18, // Alt
                        40, // Down
                        35, // End
                        27, // Escape
                        36, // Home
                        37, // Left
                        34, // Page Down
                        33, // Page Up
                        39, // Right
                        38  // Up
                     ];


    // disable pasting to avoid introducing marked-up text
    editable.on('paste', function(event) {
        event.preventDefault();
        return false;
    });

    // disable drag-and-drop to avoid introducing marked-up text
    editable.on('dragover drop', function(event) {
        event.preventDefault();
        return false;
    });

    // have to catch return key presses on the keydown (to use preventDefault)
    editable.on('keydown', function(event) {
        var code = (event.keyCode ? event.keyCode : event.which);
        // return (13) or enter (108) key pressed
        if(code == 13 || code == 108) {
            event.preventDefault();
            return false;
        } else if (msg_length >= max_msg_length && allow_keys.indexOf(code) === -1) {
            event.preventDefault();
            return false;
        } else {
            helperTextDisappear();
            msg_length = $('#message_form_editable').text().length;
        }
    });

    // catch deletes and undos on keyup (after text has been edited)
    editable.on('keyup', function(event) {
        syncFriendBoxes();
        var code = (event.keyCode ? event.keyCode : event.which);

        // Doing this here rather than the keydown because the alert seems to cause trouble with the preventDefault() to avoid the input
        if (msg_length >= max_msg_length && allow_keys.indexOf(code) === -1 && code != 13 && code != 108) {
            alert("Please limit your message to fewer than "+max_msg_length+" characters.");
        }
    });


    // now set up the manual add dropdown
    var pickFriends = [], friend, fbid;
    for (fbid in friendFromFbid) {
        friend = friendFromFbid[fbid];
        pickFriends.push({'value': friend.fbid, 'label': friend.name});
    }
    setDropdown(pickFriends);

}); // document ready


// This line makes this file show up properly in the Chrome debugger
//# sourceURL=faces_and_msg.js
