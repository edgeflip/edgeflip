/* ALL TEH CODES */









/* who user has selected to share with

this should probably turn to a parameter instead of global
*/
var recips = []; // List to hold currently selected mention tag recipient fb ids
function selectedIdx(fbid) { // do this the hard way since some versions of IE don't play indexOf()
  for(var i=0; i<recips.length; i++) {
    if (recips[i] == fbid) return i;
  }
  return -1;
}
function isSelected(fbid) {
  return (selectedIdx(fbid) != -1);
}

function getRecipElts() {
    return $('#message_form_editable .message_friend_name');
}
function getRecipIds() {
    var recipElts = getRecipElts();
    for (var i=0; i<recipElts.length; i++) {
        var recipId = recipElts[i].id;

    }

}




function htmlFriendManual(fbid, name) {
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
function activateSelectButton() {
    return activateButton(buttons, 1);
}
function activateSuggestButton() {
    return activateButton(buttons, 2);
}
function activateShareButton() {
    return activateButton(buttons, 3);
}




/* makes an HTML snippet - used to create message to share with friends

XXX may never be called w/ forMsg=false?

 */
//function spanStr(id, forMsg) {
//	// forMsg should be true to return code for the message textarea and false for suggested messages
//
//	// Yeah, I know there's a "right" way to do this, but then, I wasn't even supposed to be here today...
//	var ret;
//	if (forMsg) {
//		ret = "<span class='msg_friend_name msg-txt-friend' id='msg-txt-friend-"+id+"' contentEditable='False'>"+fbnames[id]+"<span class='msg_x' onClick='msgRemove("+id+");'>x</span></span>"
//	} else {
//		ret = "<span class='msg_friend_name msg-sugg-friend'>"+fbnames[id]+"<span class='msg_x' onClick='msgRemove("+id+");'>x</span></span>"
//	}
//	return ret
//}
function spanStr(id) {
	return "<span class='msg_friend_name' id='msg-txt-friend-"+id+"' contentEditable='False'>"+fbnames[id]+"<span class='msg_x' onClick='msgRemove("+id+");'>x</span></span>"
}


/* return a human-friendly string from friends

list of friends from global recips
*/
// Return a string with correctly formatted names of current recipients (eg, "Larry, Darryl, and Darryl")
//function friendNames(forMsg) {
//  // forMsg should be true to return code for the message textarea and false for suggested messages
//  forMsg = typeof forMsg !== 'undefined' ? forMsg : false;
//  var recip_str = "";
//
//  var txt_recips = [];
//  if (recips.length === 0) {
//  	if (forMsg) { return ""; }
//
//  	var divs = $("input[id*='box-']");
//  	for (var i=0; i < divs.length; i++) {
//  		txt_recips.push( parseInt(divs[i].id.split('-')[1]) );
//  	}
//
//  } else {
//  	txt_recips = recips.slice(0);
//  }
//
//  for (var i=0; i < (txt_recips.length-1); i++) {
//    recip_str += spanStr(txt_recips[i], forMsg) + ", ";
//  }
//
//  if (txt_recips.length > 2) {
//    recip_str += 'and ' + spanStr(txt_recips[txt_recips.length-1], forMsg);
//  } else if (txt_recips.length == 2) {
//    recip_str = spanStr(txt_recips[0], forMsg) + " and "+ spanStr(txt_recips[1], forMsg);
//  } else {
//    recip_str = spanStr(txt_recips[0], forMsg);
//  }
//
//  return recip_str;
//}

function friendNames() {
    switch (recips.length) {
        case 0:
            return "";
        case 1:
            return spanStr(recips[0]);
        case 2:
            return spanStr(recips[0]) + " and "+ spanStr(recips[1]);
        default:
            var recip_str = "";
            for (var i=0; i < (recips.length-1); i++) {
                recip_str += spanStr(recips[i]) + ", ";
            }
            recip_str += " and " + spanStr(recips[recips.length-1]);
            return recip_str;
    }
}



/* formats the current recips list into a blob of html for the editable message box */
function msgNamesUpdate(doFocus) {
    $('#message_form_names').html(friendNames());		// reword message in textbox
	if ( doFocus && ($('#message_form_names').length !== 0) ) {
		msgFocusEnd();
	}
}

/* runs when user picks a friend 

activated by click a friend to share with or from manual drop

*/

// refactor function to do any work necessary to select a friend
// returns true if recipient was added; false otherwise
function selectFriend(fbid) {
//    alert("selectFriend(" + fbid + ")");

	// check if the friend is already in the recips list, in which case do nothing
	if (! isSelected(fbid)) {
	   	recips.push(fbid);

//		// Append name to text area if user is writing their own message.
//		// Otherwise, adding to recipients will take care of this.
//		// Also, avoid appending if this div already exists -- might have been re-created by a user hitting undo after a manual delete.
//		if ( ($('#other_msg .preset_names').length === 0) && ($('#msg-txt-friend-'+fbid).length === 0) ) {
//	    	insertAtCursor('&nbsp;'+spanStr(fbid, true)+'&nbsp;');
//		}

        insertAtCursor('&nbsp;' + spanStr(fbid) + '&nbsp;');



		// if we're showing a face for the friend, check their checkbox. Otherwise, create an "added_friend" div for them
//  		if ($('#box-'+fbid).length > 0) {
//	  		  $('#box-'+fbid).prop('checked', true);
//            $('#friend-'+fbid).removeClass('unselected_friend').addClass('selected_friend');
//            $('#wrapper-'+fbid+' .xout').hide();
//            $('#wrapper-'+fbid+' .checkmark').show();
//	  	} else {
//	  		$("#picked_friends_container").append("<div class='added_friend' id='added-"+fbid+"'>"+fbnames[fbid]+"<div class='added_x' onClick='removeFriend("+fbid+");'>x</div></div>");
//	  	}

  		if ($('#wrapper-'+fbid).length > 0) {
            $('#friend-'+fbid).removeClass('friend_box_unselected').addClass('friend_box_selected');
            $('#wrapper-'+fbid+' .xout').hide();
            $('#wrapper-'+fbid+' .checkmark').show();
	  	} else {
	  		$('#picked_friends_container').append(htmlFriendManual(fbid, fbnames[fbid]))
	  	}

//        alert("hi 2");




//        if (!$('#do_share_button').hasClass('button_active')) {
//            $('#check_em_all').removeClass('active_small').addClass('inactive_small');
//            $('#sugg_msg').removeClass('inactive_small').addClass('active_small');
//        }
        activateSuggestButton();

  		return true;
  	} else {
		return false;
	}
}

/* runs when user deselects a friend 

activated by unclick a friend to share with or from manual drop or in edit message

*/
// refactor function to do any work necessary to unselect a friend
// returns true if recipient was removed; false otherwise
function unselectFriend(fbid) {
//    alert("unselectFriend(" + fbid + ")");

//	var idx = recips.indexOf(fbid);
    var idx = selectedIdx(fbid);
    if (idx !== -1) {
		recips.splice(idx, 1);
//		$('#box-'+fbid).prop('checked', false); // uncheck the box (if it exists)
		$('#added-'+fbid).remove();			  	// remove the manually added friend (if it exists)
		$('#msg-txt-friend-'+fbid).remove();	// remove the friend from the message
        $('#friend-'+fbid).removeClass('friend_box_selected').addClass('friend_box_unselected');
        $('#wrapper-'+fbid+' .xout').show();
        $('#wrapper-'+fbid+' .checkmark').hide();
		return true;
	} else {
		return false;
	}
}


// When the user clicks the 'x' on a name in the message textarea
function msgRemove(id) {
	unselectFriend(id);
	msgNamesUpdate(false); // don't move cursor to end because use is working in text area
}

/* focuses & moves cursor to end of content-editable div */
function msgFocusEnd() {
	$('#message_form_editable').focus();

	// grabbed from stackoverflow (http://stackoverflow.com/questions/1125292/how-to-move-cursor-to-end-of-contenteditable-entity)
	var contentEditableElement = document.getElementById('message_form_editable');
	var range,selection;
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
// Thank you stackoverflow! http://stackoverflow.com/questions/6690752/insert-html-at-cursor-in-a-contenteditable-div
function insertAtCursor(html) {
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

	    var recips_removed = handleDeleted();
	    if (recips_removed) {
	    	$('.suggested_msg .preset_names').html(friendNames(false));
	    }

	} else {
		$('#message_form_editable').append(html);
		msgFocusEnd();
	}
}

/* */
// more stackoverflow... http://stackoverflow.com/questions/8339857/how-to-know-if-selected-text-is-inside-a-specific-div/8340432#8340432
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
            for (var i = 0; i < sel.rangeCount; ++i) {
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

// If the user happens to manually delete a recipient while editing the message
function handleDeleted() {
  var recips_removed = false;
  var curr_recips = recips.slice(0);
  for (var i = 0; i < curr_recips.length; i++) {
  	var fbid = curr_recips[i];
  	if ($('#msg-txt-friend-'+fbid).length === 0 ) {
  		unselectFriend(fbid);
  		recips_removed = true;
  	}
  }
  return recips_removed;
}

// If the user hits "undo" and manages to add back a deleted recipient
function handleUndo() {
  var recips_added = false;
  var divs = $(".msg-txt-friend");
  for (var i = 0; i < divs.length; i++) {
  	var fbid = parseInt(divs[i].id.split('-')[3]);
  	var id_added = selectFriend(fbid);
  	recips_added = id_added || recips_added;	// might be able to do this in one line, but not clear selectFriend() will always get called once recips_added set to true...
  }
  return recips_added;
}

/* populates message div w/ suggested text */


function useSuggested(msgs) {
    recordEvent('suggest_message_click');

    //	$('#other_msg').html($(msgID).html());

    // If they don't have anyone checked, using the suggested message adds everyone
	if (recips.length === 0) {
		selectAll(true);
	}
	//$('#other_msg .preset_names').html(friendNames(true));

    // grab the pre and post off the front of the queue and stick 'em back on the end
    var msgPair = msgs.shift();
    msgs.push(msgPair);

    var msgPre = msgPair[0];
    var msgPost = msgPair[1];
    var msg = msgPre + '<span class="preset_names">' + friendNames(true) + '</span>' + msgPost;
    $('#message_form_editable').html(msg);

//    if (!$('#do_share_button').hasClass('active_button')) {
//        $('#sugg_msg').removeClass('active_small').addClass('inactive_small');
//        $('#do_share_button').removeClass('inactive_button').addClass('active_button');
//    }
    activateShareButton();

	msgFocusEnd();
}



/* selects all friends */
function selectAll(skipRecord) {

    if (!skipRecord) {
        recordEvent('select_all_click');
    }

//    if (!$('#do_share_button').hasClass('active_button')) {
//        $('#check_em_all').removeClass('active_small').addClass('inactive_small');
//        $('#sugg_msg').removeClass('inactive_small').addClass('active_small');
//    }
    activateSuggestButton();

    // Have to filter for visible because a friend div might be hidden
    // while awaiting response of an ajax suppression call...

//	var divs = $(".friend_box:visible input[id*='box-']:not(:checked)");
	var divs = $(".friend_box:visible");

  	for (var i=0; i < divs.length; i++) {
  		var fbid = parseInt(divs[i].id.split('-')[1]);
		selectFriend(fbid);
	}

	msgNamesUpdate(true);

}

// Toggle the recipient state of a friend upon checking or unchecking
function toggleFriend(fbid) {
//  alert("toggleFriend(" + fbid + ")");

  if (isSelected(fbid)) {
  	unselectFriend(fbid);
  }
  else {
  	selectFriend(fbid);
  }

//  if ($('#box-'+fbid).is(':checked')) {
//  	selectFriend(fbid);
//  } else {
//  	unselectFriend(fbid);
//  }

  msgNamesUpdate(true);
}

/*
zzz
// Quick function to allow for clicking name or image to toggle friend
// selected state in addition to clicking on the checkbox directly.
// Just need to toggle the checkbox first, then proceed as if it had
// been clicked directly.
function faceClick(fbid) {

    if (recips.length >= 10 && !$('#box-'+fbid).prop('checked')) {
        alert("Sorry: only ten friends can be tagged.");
        return false;
    }

    $('#box-'+fbid).prop('checked', !$('#box-'+fbid).prop('checked'));
    toggleFriend(fbid);
}
*/

/* called when some suppress friend (X in faces list) */
// Called when someone suppresses a friend by clicking the 'x'
function doReplace(old_fbid) {

	var div_id = '#wrapper-'+old_fbid;

	// Remove the friend from the messages
	unselectFriend(old_fbid);

    // Hide the suppressed div immediately, because the response to
    // the ajax call can be a little sluggish...
    $(div_id).hide();

	if (nextidx < friends.length) {
		// Figure out the new friend
        // Note that we're HTML-unescaping the first and last name to send back
        // to the server for templating -- the template is going to escape these
        // and we don't want them getting escaped twice! Hockey & ugly, I know,
        // but this will work until we move to a smarter system of front-end
        // templating...
		var friend = friends[nextidx];
		var id = friend['id'];
		var fname = $("<div/>").html(friend['fname']).text();
		var lname = $("<div/>").html(friend['lname']).text();

		// Update the friends shown
		friendHTML(old_fbid, id, fname, lname, div_id);

		nextidx++;
	} else {
		// No new friends to add, so just remove this one
		// (note that we have to remove rather than hide the element to avoid avoid accidentally
		// including the friend in the message that gets sent!)
		friendHTML(old_fbid, '', '', '', div_id);
		// $(div_id).remove();
	}

	// Update the message text with the new names
	msgNamesUpdate(true);
}


// Ajax call to tell our server the friend has been suppressed and get the HTML for the next one
function friendHTML(oldid, id, fname, lname, div_id) {

	var new_html;
	var userid = myfbid; // myfbid should get set globablly upon login/auth
	var appid = {{ fbParams.fb_app_id }};
	var content = '{{ fbParams.fb_app_name }}:{{ fbParams.fb_object_type }} {{ fbParams.fb_object_url | safe }}';

	var params = JSON.stringify({
		userid: userid,
		appid: appid,
		content: content,
		oldid: oldid,
		newid: id,
		fname: fname,
		lname: lname,
		sessionid: sessionid,	// global session id was pulled in from query string above
        campaignid: campaignid, // similarly, campaignid and contentid pulled into frame_faces.html from jinja
        contentid: contentid
	});

	$.ajax({
		type: "POST",
		url: '/suppress',
		contentType: "application/json",
		dataType: 'html',
		data: params,
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
                $(div_id).show();
			} else {
                // We hid it above, but still need to actually remove it if there's
                // no new friend coming in (otherwise, a select all will still add this friend...)
				$(div_id).remove();
			}
			var header_efsid = jqXHR.getResponseHeader('X-EF-SessionID');
			sessionid = header_efsid || sessionid;
		}
	});

}

/* hits facebook API */
// Called when someone actually shares a message
function doShare() {
    recordEvent('share_click');

    var fb_app_name = '{{ fbParams.fb_app_name }}';
    var fb_action_type = '{{ fbParams.fb_action_type }}';
    var fb_object_type = '{{ fbParams.fb_object_type }}';
    var fb_object_url = '{{ fbParams.fb_object_url | safe }}';

	// Quick checks: has the user selected a message and at least one friend with whom to share?
	var msg = "";

	if (recips.length == 0) {
		var use_all = confirm("You haven't chosen any friends to share with.\n\nClick OK to share with all suggested friends or CANCEL to return to the page.");
		if (use_all) {
			selectAll(true);
		} else {
			return;
		}
	}

    helperTextDisappear();
    $('#friends_div').hide();
    $('#progress h2').html('S e n d i n g . . .');
    $('#progress').show();

	// The message text will just be whatever is in #other_msg when the user hits send
	// but we need to clean it up a little bit first...
	handleDeleted();
	handleUndo();
	msgNamesUpdate(false);

    alert($('#message_form_editable').html());

	for (var i=0; i < recips.length; i++) {
		// FB format for mention tags: @[fbid]
		$('#msg-txt-friend-'+recips[i]).replaceWith("@[" + recips[i] + "]");
	}
	if ($('#message_form_editable .preset_names').length > 0) {
		$('#message_form_editable .preset_names').replaceWith($('#message_form_editable .preset_names').text());
	}

	msg = $('#message_form_editable').text();
	msg = msg.replace(/[\n\r]/g, ' ');
	msg = msg.substring(0, 1500); // Limit submissions to 1,500 characters (different from keydown to allow for possibility that fbid's are longer)

    alert("sharing msg: " + msg);
    return;

	// The actual call to do the sharing
	FB.api(
		'/me/' + fb_app_name + ':' + fb_action_type,
		'post',
		{ fb_object_type: fb_object_url, message: msg },
		function(response) {
			if (!response || response.error) {
				// alert('Error occured ' + response.error.message);
                // show an alert and then redirect them to wherever the client wants them to go in this case...
                recordEvent('share_fail', response.error);
                alert("Sorry. An error occured sending your message to facebook. Please try again later.");
                top.location = errorURL; // set in frame_faces.html via Jinja
			} else {
                // thank you page redirect happens in recordShare()
				recordShare(response.id);
				// alert('Post was successful! Action ID: ' + response.id);
			}
	  	}
	);
}


/* records share event on edgeflip servers; redirects user to thank you page */
function recordShare(actionid) {
	var new_html;
	var userid = myfbid; // myfbid should get set globablly upon login/auth
	var appid = {{ fbParams.fb_app_id }};
	var content = '{{ fbParams.fb_app_name }}:{{ fbParams.fb_object_type }} {{ fbParams.fb_object_url | safe }}';

	var params = JSON.stringify({
		userid: userid,
		actionid: actionid,
		appid: appid,
		content: content,
		friends: recips,
        eventType: 'shared',
		sessionid: sessionid,	// global session id was pulled in from query string above
        campaignid: campaignid, // similarly, campaignid and contentid pulled into frame_faces.html from jinja
        contentid: contentid
	});

	$.ajax({
		type: "POST",
		url: '/record_event',
		contentType: "application/json",
		dataType: 'html',
		data: params,
		error: function(jqXHR, textStatus, errorThrown) {
			// Even if recording the event on our servers failed, we should send them on their way...
            top.location = thanksURL; // set in frame_faces.html via Jinja
		},
		success: function(data, textStatus, jqXHR) {
			var header_efsid = jqXHR.getResponseHeader('X-EF-SessionID');
			sessionid = header_efsid || sessionid;
            top.location = thanksURL; // set in frame_faces.html via Jinja
		}
	});

}

// record events other than the share (so, no redirect).
// should obviously combine with above at some point, but
// just want to have something working now...
function recordEvent(eventType, errorMsg) {

    var userid = myfbid;
    var appid = {{ fbParams.fb_app_id }};
    var content = '{{ fbParams.fb_app_name }}:{{ fbParams.fb_object_type }} {{ fbParams.fb_object_url | safe }}';

    var params = JSON.stringify({
        userid: userid,
        appid: appid,
        content: content,
        eventType: eventType,
        sessionid: sessionid,   // global session id was pulled in from query string above
        campaignid: campaignid, // similarly, campaignid and contentid pulled into frame_faces.html from jinja
        contentid: contentid,
        errorMsg: errorMsg
    });

    $.ajax({
        type: "POST",
        url: '/record_event',
        contentType: "application/json",
        dataType: 'html',
        data: params,
        error: function(jqXHR, textStatus, errorThrown) {
            // Nothing to do here...
        },
        success: function(data, textStatus, jqXHR) {
            var header_efsid = jqXHR.getResponseHeader('X-EF-SessionID');
            sessionid = header_efsid || sessionid;
        }
    });

}

function helperTextDisappear() {
    $('#helper_txt').remove();
}

