var recips = []; // List to hold currently selected mention tag recipients


// Return a string with correctly formatted names of current recipients (eg, "Larry, Darryl, and Darryl")
function friendNames() {
  recip_str = "";

  if (recips.length == 0) { return ""; }

  for (i=0; i < (recips.length-1); i++) {
    recip_str += "<span class='msg_friend_name'>" + fbnames[recips[i]] + "</span>, ";
  }

  if (recips.length > 2) {
    recip_str += 'and ' + "<span class='msg_friend_name'>" + fbnames[recips[recips.length-1]] + "</span>";
  } else if (recips.length == 2) {
    recip_str = "<span class='msg_friend_name'>" + fbnames[recips[0]] + "</span> and <span class='msg_friend_name'>" + fbnames[recips[1]] + "</span>";
  } else {
    recip_str = "<span class='msg_friend_name'>" + fbnames[recips[0]] + "</span>";
  }

  return recip_str;
}


// Toggle the recipient state of a friend upon checking or unchecking
function toggleFriend(fbid) {
  var idx = recips.indexOf(fbid);
  if (idx > -1) { recips.splice(idx, 1); }
  $('#msg-txt-friend-'+fbid).remove();

  if ($('#box-'+fbid).is(':checked')) {
    recips.push(fbid);
    $('#other_msg').append(' <span class="msg_friend_name msg-txt-friend" id="msg-txt-friend-'+fbid+'" contentEditable="False">'+fbnames[fbid]+'</span> ');
  }

  $('.preset_names').html(friendNames());

}


// Toggle state of the user-entered message text field based on which radio button is selected
function updateMsg() {

	var msg_type = $('input:radio[name=msg]:checked').val();
	if (msg_type === "other") {
		$('#other_msg').show().focus();

		// Is the default text still in there? If so, highlight it for easy replacement
		var reptxt = $('#other_msg').text().indexOf("{{ msg_other_init }}");

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
		$('#other_msg').append(' <span class="msg_friend_name msg-txt-friend" id="msg-txt-friend-'+id+'" contentEditable="False">'+fbnames[id]+'</span> ');

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
	$('.preset_names').html(friendNames());
}


// Ajax call to tell our server the friend has been suppressed and get the HTML for the next one
function friendHTML(oldid, id, fname, lname, div_id) {

	var new_html;
	var userid = myfbid; // myfbid should get set globablly upon login/auth
	var appid = {{ fb_app_id }};
	var content = '{{ fb_app_name }}:{{ fb_object_type }} {{ fb_object_url }}';

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
	var msg_type = $('input:radio[name=msg]:checked').val();
	var msg = "";

	if (!msg_type || msg_type === "") { alert('Please choose a message to send or write your own'); return;}
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


	if (msg_type === "msg1") {
		msg = "{{ msg1_pre }}"+msg_recips+"{{ msg1_post }}";
	} else if (msg_type === "msg2") {
		msg = "{{ msg2_pre }}"+msg_recips+"{{ msg2_post }}";
	} else if (msg_type === "other") {
		for (i=0; i < recips.length; i++) {
			$('#msg-txt-friend-'+recips[i]).replaceWith("@[" + recips[i] + "]");
		}
		msg = $('#other_msg').html();
	} else {
		alert("Ruh-Roh!!"); // I don't know how we go here, but here we are...
	}


	// The actual call to do the sharing
	// In the future, we'll probably want to parametarize this for different types of actions
	FB.api(
// FIXME: GET BACK TO TEMPLATE HERE!!!!!!!!
//		'/me/{{ fb_app_name }}:{{ fb_action_type }}',
		'/me/read',
		'post',
		{ 
		  {{ fb_object_type }}: '{{ fb_object_url }}',
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
