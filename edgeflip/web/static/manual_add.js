/* widget for manually adding a friend */


// Set up the autofill drop-down for manually adding friends
$(function() {

	$( "#manual_input" ).autocomplete({
		minLength: 0,
		source: function(request, response) {
			var filteredArray = $.map(pick_friends, function(item) {
	        	var patt = new RegExp('\\b'+request.term, 'i');
	        	if( patt.test(item.label) ){
	            	return item;
	        	} else {
	            	return null;
	        	}
    		});
    		response(filteredArray);
		},
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
					selectFriend(ui.item.value);
					msgNamesUpdate(false);
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
	unselectFriend(fbid);
	msgNamesUpdate(false);
}
