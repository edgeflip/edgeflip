var recips = []; // List to hold currently selected mention tag recipients


function spanStr(id, forMsg) {
	// forMsg should be true to return code for the message textarea and false for suggested messages

	// Yeah, I know there's a "right" way to do this, but then, I wasn't even supposed to be here today...
	var ret;
	if (forMsg) {
		ret = "<span class='msg_friend_name msg-txt-friend' id='msg-txt-friend-"+id+"' contentEditable='False'>"+fbnames[id]+"<span class='msg_x' onClick='msgRemove("+id+");'>x</span></span>"
	} else {
		ret = "<span class='msg_friend_name msg-sugg-friend'>"+fbnames[id]+"<span class='msg_x' onClick='msgRemove("+id+");'>x</span></span>"
	}
	return ret
}

// Return a string with correctly formatted names of current recipients (eg, "Larry, Darryl, and Darryl")
function friendNames(forMsg) {
  // forMsg should be true to return code for the message textarea and false for suggested messages
  forMsg = typeof forMsg !== 'undefined' ? forMsg : false;
  var recip_str = "";

  var txt_recips = [];
  if (recips.length === 0) { 
  	if (forMsg) { return ""; }

  	var divs = $("input[id*='box-']");
  	for (var i=0; i < divs.length; i++) {
  		txt_recips.push( parseInt(divs[i].id.split('-')[1]) );
  	}

  } else {
  	txt_recips = recips.slice(0);
  }

  for (var i=0; i < (txt_recips.length-1); i++) {
    recip_str += spanStr(txt_recips[i], forMsg) + ", ";
  }

  if (txt_recips.length > 2) {
    recip_str += 'and ' + spanStr(txt_recips[txt_recips.length-1], forMsg);
  } else if (txt_recips.length == 2) {
    recip_str = spanStr(txt_recips[0], forMsg) + " and "+ spanStr(txt_recips[1], forMsg);
  } else {
    recip_str = spanStr(txt_recips[0], forMsg);
  }

  return recip_str;
}

function msgNamesUpdate(doFocus) {

	$('.suggested_msg .preset_names').html(friendNames(false)); // reword suggested messages
	$('#other_msg .preset_names').html(friendNames(true));		// reword message in textbox

	if ( doFocus && ($('#other_msg .preset_names').length !== 0) ) {
		msgFocusEnd();
	}

}

// refactor function to do any work necessary to select a friend
// returns true if recipient was added; false otherwise
function selectFriend(fbid) {

	// check if the friend is already in the recips list, in which case do nothing
	if (recips.indexOf(fbid) === -1) {
		recips.push(fbid);

		// Append name to text area if user is writing their own message.
		// Otherwise, adding to recipients will take care of this.
		// Also, avoid appending if this div already exists -- might have been re-created by a user hitting undo after a manual delete.
		if ( ($('#other_msg .preset_names').length === 0) && ($('#msg-txt-friend-'+fbid).length === 0) ) {
	    	insertAtCursor('&nbsp;'+spanStr(fbid, true)+'&nbsp;');
		}

		// if we're showing a face for the friend, check their checkbox. Otherwise, create an "added_friend" div for them
  		if ($('#box-'+fbid).length > 0) {
	  		$('#box-'+fbid).prop('checked', true);
	  	} else {
	  		$("#picked_friends_container").append("<div class='added_friend' id='added-"+fbid+"'>"+fbnames[fbid]+"<div class='added_x' onClick='removeFriend("+fbid+");'>x</div></div>");
	  	}

  		return true;
  	} else {
		return false;
	}
}

// refactor function to do any work necessary to unselect a friend
// returns true if recipient was removed; false otherwise
function unselectFriend(fbid) {
	var idx = recips.indexOf(id);
	if (idx !== -1) {

		recips.splice(idx, 1);
		$('#box-'+id).prop('checked', false); // uncheck the box (if it exists)
		$('#added-'+id).remove();			  // remove the manually added friend (if it exists)
		$('#msg-txt-friend-'+id).remove();	  // remove the friend from the message

		return true;
	} else {
		return false;
	}
}


// When the user clicks the 'x' on a name in the message textarea
function msgRemove(id) {
	// var idx = recips.indexOf(id);
	// recips.splice(idx, 1);
	// $('#box-'+id).prop('checked', false); // uncheck the box (if it exists)
	// $('#added-'+id).remove();			  // remove the manually added friend (if it exists)
	// $('#msg-txt-friend-'+id).remove();	  // remove the friend from the message

	uselectFriend(id);
	msgNamesUpdate(false); // don't move cursor to end because use is working in text area

}

function msgFocusEnd() {
	$('#other_msg').focus();

	// grabbed from stackoverflow (http://stackoverflow.com/questions/1125292/how-to-move-cursor-to-end-of-contenteditable-entity)
	var contentEditableElement = document.getElementById('other_msg');
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

// Thank you stackoverflow! http://stackoverflow.com/questions/6690752/insert-html-at-cursor-in-a-contenteditable-div
function insertAtCursor(html) {
    var sel, range;
    if ( elementContainsSelection($('#other_msg').get(0)) ) {
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
		$('#other_msg').append(html);
		msgFocusEnd();
	}
}

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

function filter_newlines(div) {
    var node, prev, _i, _len, _ref, _results;
    prev = null;
    _ref = div.contents();
    _results = [];
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      node = _ref[_i];
      if (node.nodeType === 3) {
        node.nodeValue = node.nodeValue.replace('\n', '');
        if (prev) {
          node.nodeValue = prev.nodeValue + node.nodeValue;
          $(prev).remove();
        }
        _results.push(prev = node);
      } else if (node.tagName.toLowerCase() === 'br') {
        _results.push($(node).remove());
      } else {
        $(node).css('display', 'inline');
        filter_newlines($(node));
        _results.push(prev = null);
      }
    }
    return _results;
}

// If the user happens to manually delete a recipient while editing the message
function handleDeleted() {
  var recips_removed = false;
  var curr_recips = recips.slice(0);
  for (var i = 0; i < curr_recips.length; i++) {
  	var fbid = curr_recips[i];
  	if ($('#msg-txt-friend-'+fbid).length === 0 ) {
  		// var idx = recips.indexOf(fbid);
  		// recips.splice(idx, 1);
  		// $('#box-'+fbid).prop('checked', false);
  		// $('#added-'+fbid).remove();
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
  	// if (recips.indexOf(fbid) === -1) {
  	//	recips.push(fbid);
  	//	if ($('#box-'+fbid).length > 0) {
	//  	$('#box-'+fbid).prop('checked', true);
	//  } else {
	//  	$("#picked_friends_container").append("<div class='added_friend' id='added-"+fbid+"'>"+fbnames[fbid]+"<div class='added_x' onClick='removeFriend("+fbid+");'>x</div></div>");
	//  }
  	//	recips_added = true;
  	// }
  }
  return recips_added;
}


function useSuggested(msgID) {
	$('#other_msg').html($(msgID).html());

	// If they don't have anyone checked, using the suggested message adds everyone
	if (recips.length === 0) {

		// var divs = $("input[id*='box-']");
		// divs.prop('checked', true);
	 	// for (var i=0; i < divs.length; i++) {
	 	// 		recips.push( parseInt(divs[i].id.split('-')[1]) );
		// }

		checkAll();

	}
	$('#other_msg .preset_names').html(friendNames(true));

	msgFocusEnd();
}

function checkAll() {

	var divs = $("input[id*='box-']:not(:checked)");
	// divs.prop('checked', true);
  	for (var i=0; i < divs.length; i++) {
  		var fbid = parseInt(divs[i].id.split('-')[1]);
  		// recips.push(fbid);
	    // if ($('#other_msg .preset_names').length === 0) {
	    //	// Only append name if user is writing their own message. Otherwise, friendNames() call below will take care of this.
		//    insertAtCursor('&nbsp;'+spanStr(fbid, true)+'&nbsp;');
		// }

		selectFriend(fbid);
	}

	msgNamesUpdate(true);

}

// Toggle the recipient state of a friend upon checking or unchecking
function toggleFriend(fbid) {
  // var idx = recips.indexOf(fbid);
  // if (idx > -1) { recips.splice(idx, 1); }
  // $('#msg-txt-friend-'+fbid).remove();

  // if ($('#box-'+fbid).is(':checked')) {
  //   recips.push(fbid);
  //   if ($('#other_msg .preset_names').length === 0) {
  //   	// Only append name if user is writing their own message. Otherwise, friendNames() call below will take care of this.
  //     insertAtCursor('&nbsp;'+spanStr(fbid, true)+'&nbsp;');
  //   }
  // }

  if ($('#box-'+fbid).is(':checked')) {
  	selectFriend(fbid);
  } else {
  	unselectFriend(fbid);
  }

  msgNamesUpdate(true);

}

// Called when someone suppresses a friend by clicking the 'x'
function doReplace(old_fbid) {

	var div_id = '#friend-'+old_fbid;

	// Remove the friend from the messages
	unselectFriend(old_fbid);
	// var idx = recips.indexOf(old_fbid);
	// if (idx > -1) { recips.splice(idx, 1); }
	// $('#msg-txt-friend-'+old_fbid).remove();

	if (nextidx < friends.length) {
		// Figure out the new friend
		var friend = friends[nextidx];
		var id = friend['id'];
		var fname = friend['fname'];
		var lname = friend['lname'];

		// Update the friends shown
		friendHTML(old_fbid, id, fname, lname, div_id);

		// Add the new friend to the list of message tags (since they'll start off pre-checked)
		selectFriend(id);
		// recips.push(id);
    	// if ($('#other_msg .preset_names').length === 0) {
		// 		insertAtCursor('&nbsp;'+spanStr(id, true)+'&nbsp;');
		// }

		nextidx++;
	} else {
		// No new friends to add, so just remove this one
		// (note that we have to remove rather than hide the element to avoid avoid accidentally
		// including the friend in the message that gets sent!)
		$(div_id).remove();
	}

	// Update the message text with the new names
	msgNamesUpdate(true);
}


// Ajax call to tell our server the friend has been suppressed and get the HTML for the next one
function friendHTML(oldid, id, fname, lname, div_id) {

	var new_html;
	var userid = myfbid; // myfbid should get set globablly upon login/auth
	var appid = {{ fbParams.fb_app_id }};
	var content = '{{ fbParams.fb_app_name }}:{{ fbParams.fb_object_type }} {{ fbParams.fb_object_url }}';

	var params = JSON.stringify({
		userid: userid,
		appid: appid,
		content: content,
		oldid: oldid,
		newid: id,
		fname: fname,
		lname: lname
	});

	$.ajax({
		type: "POST",
		url: '/suppress',
		contentType: "application/json",
		dataType: 'html',
		data: params,
		error: function(jqXHR, textStatus, errorThrown) {
					new_html = 'Error pants: ' + textStatus + ' ' + errorThrown;
					$(div_id).replaceWith(new_html);
		},
		success: function(data) {
					new_html = data;
					$(div_id).replaceWith(new_html);
		}
	});

}


// Called when someone actually shares a message
function doShare() {

	// Quick checks: has the user selected a message and at least one friend with whom to share?
	var msg = "";
	var msg_recips = "";

	if (recips.length == 0) { alert('Please choose at least one friend to share with.'); return; }

	// FB format for mention tags: @[fbid]
	for (var i=0; i < (recips.length-1); i++) {
		msg_recips += "@[" + recips[i] + "], ";
	}

	if (recips.length > 2) {
		msg_recips += 'and ' + "@[" + recips[recips.length-1] + "]";
	} else if (recips.length == 2) {
		msg_recips = "@[" + recips[0] + "] and @[" + recips[1] + "]";
	} else {
		msg_recips = "@[" + recips[0] + "]";
	}

	// The message text will just be whatever is in #other_msg when the user hits send
	// but we need to clean it up a little bit first...
	for (var i=0; i < recips.length; i++) {
		$('#msg-txt-friend-'+recips[i]).replaceWith("@[" + recips[i] + "]");
	}
	if ($('#other_msg .preset_names').length > 0) {
		$('#other_msg .preset_names').replaceWith($('#other_msg .preset_names').text());
	}
	// $('#other_msg div').remove();
	msg = $('#other_msg').text();
	msg = msg.replace(/[\n\r]/g, ' ');
	// TODO: Determine maximum allowed length of message and limit submission to this length.

	// The actual call to do the sharing
	// In the future, we'll probably want to parametarize this for different types of actions
	FB.api(
		'/me/{{ fbParams.fb_app_name }}:{{ fbParams.fb_action_type }}',
		'post',
		{ 
		  {{ fbParams.fb_object_type }}: '{{ fbParams.fb_object_url }}',
		  message: msg
		},
		function(response) {
			if (!response || response.error) {
				alert('Error occured ' + response.error.message);
			} else {
				// Eventually, this should just redirect to a thank you page
				alert('Post was successful! Action ID: ' + response.id);
			}
	  	}
	);
}
