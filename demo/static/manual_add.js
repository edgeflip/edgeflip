
// Set up the autofill drop-down for manually adding friends
$(function() {

	$( "#manual_input" ).autocomplete({
		minLength: 0,
		source: pick_friends,
		focus: function( event, ui ) {
			$( "#manual_input" ).val( ui.item.label );
			return false;
		},
		select: function( event, ui ) {

			// Only add a friend if they haven't already been added (and aren't already provided)
			if (!( $("#added-"+ui.item.value).length > 0 || $("#friend-"+ui.item.value).length > 0 ) ) {

				if ($(".added_friend").length >= 3) {
					alert("Sorry: only three friends can be added manually.");
				} else {

					$("#picked_friends_container").append("<div class='added_friend' id='added-"+ui.item.value+"'>"+ui.item.label+"<div class='added_x' onClick='removeFriend("+ui.item.value+");'>x</div></div>");

					var idx = recips.indexOf(ui.item.value);
					if (idx > -1) { recips.splice(idx, 1); }
					$('#msg-txt-friend-'+ui.item.value).remove();

					recips.push(ui.item.value);
					$('#other_msg').append(' <span class="msg_friend_name msg-txt-friend" id="msg-txt-friend-'+ui.item.value+'" contentEditable="False">'+ui.item.label+'</span> ');

					$('.preset_names').html(friendNames());

				}
			}
			$("#manual_input").val('');
			return false;
		}
	})
	.data( "uiAutocomplete" )._renderItem = function( ul, item ) {
		return $( "<li>" )
			.append( "<a>" + "<img src='http://graph.facebook.com/" +item.value+"/picture' height=25 /> " + item.label + "</a>" )
			.appendTo( ul );
	};

});

// Called when the user removes a manually added friend
function removeFriend(fbid) {
	$("#added-"+fbid).remove();

	var idx = recips.indexOf(fbid);
	if (idx > -1) { recips.splice(idx, 1); }
	$('#msg-txt-friend-'+fbid).remove();

	$('.preset_names').html(friendNames());
}
