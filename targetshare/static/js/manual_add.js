/* widget for manually adding a friend */


// Set up the autofill drop-down for manually adding friends
function setDropdown(friends) {
    var renderFriend = function( ul, item ) {
        return $( "<li>" )
            .append( "<a>" + "<img src='http://graph.facebook.com/" +item.value+"/picture' height=25 /> " + item.label + "</a>" )
            .appendTo( ul );
    };

    $(".manual_input").autocomplete({
        minLength: 0,
        source: function(request, response) {
            var input = $.ui.autocomplete.escapeRegex(request.term);
            var patt = new RegExp('\\b' + input, 'i');
            var filteredArray = $.map(friends, function(item) {
                return patt.test(item.label) ? item : null;
            });
            response(filteredArray);
        },
        focus: function( evt, ui ) {
            $(this).val( ui.item.label );
            return false;
        },
        select: function( event, ui ) {
            var fbid = parseInt(ui.item.value);

            if(!isRecip(fbid)) {
                if(getRecipFbids().length >= edgeflip.faces.max_face) {
                    alertTooMany();
                } else {
                    selectFriend(fbid);
                }
            }

            $(this).val('');
            return false;
        }
    }).each(function() {
        $(this).data("uiAutocomplete")._renderItem = renderFriend;
    });
}

// Called when the user removes a manually added friend
function removeFriend(fbid) {
    unselectFriend(fbid);
}

// This line makes this file show up properly in the Chrome debugger
//# sourceURL=manual_add.js
