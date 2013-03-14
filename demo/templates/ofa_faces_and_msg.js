var recips = []; // List to hold currently selected mention tag recipients


function spanStr(id, forMsg) {
	// forMsg should be true to return code for the message textarea and false for suggested messages

	// Yeah, I know there's a "right" way to do this, but then, I wasn't even supposed to be here today...
	if (forMsg) {
		ret = "<span class='msg_friend_name msg-txt-friend' id='msg-txt-friend-"+id+"' contentEditable='False'>"+fbnames[id]+"<span class='msg_x' onClick='msgRemove("+id+");'>x</span></span>"
	} else {
		ret = "<span class='msg_friend_name msg-sugg-friend'>"+fbnames[id]+"<span class='msg_x'>x</span></span>"
	}
	return ret
}

// Return a string with correctly formatted names of current recipients (eg, "Larry, Darryl, and Darryl")
function friendNames(forMsg) {
  // forMsg should be true to return code for the message textarea and false for suggested messages
  forMsg = typeof forMsg !== 'undefined' ? forMsg : false;
  recip_str = "";

  txt_recips = [];
  if (recips.length === 0) { 
  	if (forMsg) { return ""; }

  	divs = $("input[id*='box-']");
  	for (i=0; i < divs.length; i++) {
  		txt_recips.push( parseInt(divs[i].id.split('-')[1]) );
  	}

  } else {
  	txt_recips = recips.slice(0);
  }

  for (i=0; i < (txt_recips.length-1); i++) {
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

function msgRemove(id) {
	idx = recips.indexOf(id);
	recips.splice(idx, 1);
	$('#box-'+id).prop('checked', false); // uncheck the box (if it exists)
	$('#added-'+id).remove();			  // remove the manually added friend (if it exists)
	$('#msg-txt-friend-'+id).remove();	  // remove the friend from the message

	$('.suggested_msg .preset_names').html(friendNames(false)); // reword suggested messages
	$('#other_msg .preset_names').html(friendNames(true));		// reword message in textbox

}

function msgFocus() {
	$('#other_msg').focus();

	// grabbed from stackoverflow (http://stackoverflow.com/questions/1125292/how-to-move-cursor-to-end-of-contenteditable-entity)
	contentEditableElement = document.getElementById('other_msg');
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

function useSuggested(msgID) {
	$('#other_msg').html($(msgID).html());

	// If they don't have anyone checked, using the suggested message adds everyone
	if (recips.length === 0) {

		divs = $("input[id*='box-']");
		divs.prop('checked', true);
	  	for (i=0; i < divs.length; i++) {
	  		recips.push( parseInt(divs[i].id.split('-')[1]) );
	  	}

	}
	$('#other_msg .preset_names').html(friendNames(true));

	msgFocus();
}

function checkAll() {

	divs = $("input[id*='box-']:not(:checked)");
	divs.prop('checked', true);
  	for (i=0; i < divs.length; i++) {
  		fbid = parseInt(divs[i].id.split('-')[1]);
  		recips.push(fbid);
	    if ($('#other_msg .preset_names').length === 0) {
	    	// Only append name if user is writing their own message. Otherwise, friendNames() call below will take care of this.
		    $('#other_msg').append(' '+spanStr(fbid, true)+' ');
		}
	}

	$('.suggested_msg .preset_names').html(friendNames(false));
	$('#other_msg .preset_names').html(friendNames(true));

	msgFocus();

}

// Toggle the recipient state of a friend upon checking or unchecking
function toggleFriend(fbid) {
  var idx = recips.indexOf(fbid);
  if (idx > -1) { recips.splice(idx, 1); }
  $('#msg-txt-friend-'+fbid).remove();

  if ($('#box-'+fbid).is(':checked')) {
    recips.push(fbid);
    if ($('#other_msg .preset_names').length === 0) {
    	// Only append name if user is writing their own message. Otherwise, friendNames() call below will take care of this.
	    $('#other_msg').append(' '+spanStr(fbid, true)+' ');
	}
  }

  $('.suggested_msg .preset_names').html(friendNames(false));
  $('#other_msg .preset_names').html(friendNames(true));

  msgFocus();

}


// Toggle state of the user-entered message text field based on which radio button is selected
function updateMsg() {

	// Pretty sure this is no longer called at all, but holding off on deleting for the moment...

	var msg_type = $('input:radio[name=msg]:checked').val();
	if (msg_type === "other") {
		$('#other_msg').show().focus();

		// Is the default text still in there? If so, highlight it for easy replacement
		var reptxt = $('#other_msg').text().indexOf("{{ msgParams.msg_other_init }}");

		if ( reptxt > -1 ) {

			var txtnode = document.getElementById('other_msg');

			if (document.createRange) {

				var selection = window.getSelection();
				var range = document.createRange();

				range.setStart(txtnode.firstChild, reptxt);
				range.setEnd(txtnode.firstChild, reptxt+40);
				selection.removeAllRanges();
				selection.addRange(range);

			} else {

				var range = document.body.createTextRange();
				range.moveToElementText($('#other_msg'));
				range.moveStart("character", reptxt);
				range.collapse(true);
				range.moveEnd("character", reptxt+40);
				range.select();

			}
		}
	} else {
		$('#other_msg').hide();
	}

}


// Called when someone suppresses a friend by clicking the 'x'
function doReplace(old_fbid) {

	var div_id = '#friend-'+old_fbid;

	// Remove the friend from the messages
	var idx = recips.indexOf(old_fbid);
	if (idx > -1) { recips.splice(idx, 1); }
	$('#msg-txt-friend-'+old_fbid).remove();

	if (nextidx < friends.length) {
		// Figure out the new friend
		var friend = friends[nextidx];
		var id = friend['id'];
		var fname = friend['fname'];
		var lname = friend['lname'];

		// Add the new friend to the list of message tags (since they'll start off pre-checked)
		recips.push(id);
    	if ($('#other_msg .preset_names').length === 0) {
			$('#other_msg').append(' '+spanStr(fbid, true)+' ');
		}

		// Update the friends shown
		friendHTML(old_fbid, id, fname, lname, div_id);

		nextidx++;
	} else {
		// No new friends to add, so just remove this one
		// (note that we have to remove rather than hide the element to avoid avoid accidentally
		// including the friend in the message that gets sent!)
		$(div_id).remove();
	}

	// Update the message text with the new names
	$('.suggested_msg .preset_names').html(friendNames(false));
	$('#other_msg .preset_names').html(friendNames(true));

	msgFocus();
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
//	var msg_type = $('input:radio[name=msg]:checked').val();
	var msg = "";

//	if (!msg_type || msg_type === "") { alert('Please choose a message to send or write your own'); return;}
	if (recips.length == 0) { alert('Please choose at least one friend to share with.'); return; }


	msg_recips = "";

	// FB format for mention tags: @[fbid]
	for (i=0; i < (recips.length-1); i++) {
		msg_recips += "@[" + recips[i] + "], ";
	}

	if (recips.length > 2) {
		msg_recips += 'and ' + "@[" + recips[recips.length-1] + "]";
	} else if (recips.length == 2) {
		msg_recips = "@[" + recips[0] + "] and @[" + recips[1] + "]";
	} else {
		msg_recips = "@[" + recips[0] + "]";
	}


//	if (msg_type === "msg1") {
//		msg = "{{ msgParams.msg1_pre }}"+msg_recips+"{{ msgParams.msg1_post }}";
//	} else if (msg_type === "msg2") {
//		msg = "{{ msgParams.msg2_pre }}"+msg_recips+"{{ msgParams.msg2_post }}";
//	} else if (msg_type === "other") {
//		for (i=0; i < recips.length; i++) {
//			$('#msg-txt-friend-'+recips[i]).replaceWith("@[" + recips[i] + "]");
//		}
//		msg = $('#other_msg').html();
//	} else {
//		alert("Ruh-Roh!!"); // I don't know how we go here, but here we are...
//	}

	// Now, we always take the message text from the other_msg div
	for (i=0; i < recips.length; i++) {
		$('#msg-txt-friend-'+recips[i]).replaceWith("@[" + recips[i] + "]");
	}
	if ($('#other_msg .preset_names').length > 0) {
		$('#other_msg .preset_names').replaceWith($('#other_msg .preset_names').text());
	}
	$('#other_msg div').remove();
	msg = $('#other_msg').text();

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
