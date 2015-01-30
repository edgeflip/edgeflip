/* widget for manually adding a friend */

setDropdown = (function ($, faces, sharing) {
    var profilepic = function (friend) {
        return friend.pic ? friend.pic : "https://graph.facebook.com/" + friend.uid + "/picture";
    };
    var renderFriend = function (ul, item) {
        var image = $('<img>', {'height': '25', 'src': profilepic(item.value)}),
            anchor = $('<a>').append(image, item.label),
            li = $('<li>').append(anchor);

        return li.appendTo(ul);
    };

    return function (friends) {
        // Set up the autofill drop-down for manually adding friends
        $('.manual_input').autocomplete({
            minLength: 0,
            source: function(request, response) {
                var input = $.ui.autocomplete.escapeRegex(request.term),
                    patt = new RegExp('\\b' + input, 'i'),
                    filteredArray = $.map(friends, function (item) {
                        return patt.test(item.label) ? item : null;
                    });
                response(filteredArray);
            },
            focus: function(evt, ui) {
                var escapeHtml = $('<div/>').html(ui.item.label).text();
                $(this).val(escapeHtml);
                return false;
            },
            select: function (event, ui) {
                var uid = ui.item.value.uid;

                if (!sharing.recipients.isRecipient(uid)) {
                    if (sharing.recipients.count() >= faces.max_face) {
                        sharing.alertTooMany();
                    } else {
                        sharing.selectFriend(uid);
                    }
                }

                $(this).val('');
                return false;
            }
        }).each(function () {
            $(this).data("uiAutocomplete")._renderItem = renderFriend;
        });
    };
})(jQuery, edgeflip.faces, edgeflip.sharing);

// This line makes this file show up properly in the Chrome debugger
//# sourceURL=manual_add.js
