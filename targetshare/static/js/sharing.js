edgeflip.sharing = (function ($, edgeflip) {
    /* Generic helpers */

    function isOrContains(node, container) {
        // http://stackoverflow.com/questions/8339857/how-to-know-if-selected-text-is-inside-a-specific-div/8340432#8340432
        while (node) {
            if (node === container) {
                return true;
            }
            node = node.parentNode;
        }
        return false;
    }

    function elementContainsSelection (el) {
        var selection, i;
        if (window.getSelection) {
            selection = window.getSelection();
            if (selection.rangeCount > 0) {
                for (i = 0; i < selection.rangeCount; ++i) {
                    if (!isOrContains(selection.getRangeAt(i).commonAncestorContainer, el)) {
                        return false;
                    }
                }
                return true;
            }
        } else if ((selection = document.selection) && selection.type != "Control") {
            return isOrContains(selection.createRange().parentElement(), el);
        }
        return false;
    }

    function commafy (things) {
        var body, tail;
        switch (things.length) {
            case 0:
                return "";
            case 1:
                return things[0];
            case 2:
                return things[0] + " and " + things[1];
            default:
                body = things.slice(0, -1).join(', '),
                tail = things[things.length - 1];
                return body + " and " + tail;
        }
    }

    /* sharing module definition */

    var self = {
        configure: function (options) {
            self.allFriends = options.allFriends;
            self.faceFriends = options.faceFriends;
            self.suggestedMessages = options.suggestedMessages.filter(
                // Exclude empty message suggestion pairs
                function (pair) {
                    return pair.some(function (part) {
                        return Boolean(part);
                    });
                }
            );
        }
    },
    $editable = $('#message_form_editable');

    var _lookupFbid = function (uid) {
        var friend = self.allFriends[uid],
            fbid = friend.fbid;
        return fbid ? fbid : uid;
    };
    function mapFbids (uids) {
        /* Map a single UID to an FBID or an array of UIDs to an array of FBIDs.
         *
         * If no FBID for a UID can be found, returns the UID.
         */
        return Array.isArray(uids) ? uids.map(_lookupFbid) : _lookupFbid(uids);
    }

    self.recipients = (function ($, sharing) {
        /* recipients submodule definition */
        var self = {
            containerId: 'recips_list',
            createContainerElement: function () {
                return $('<span></span>', {
                    'id': self.containerId
                });
            },
            getContainerElement: function () {
                return $('#' + self.containerId);
            },
            getElements: function () {
                /* Return the jQuery collection of selected friends.
                */
                return $editable.find('.recipient');
            },
            count: function () {
                return self.getElements().length;
            },
            getUids: function () {
                /* Return an jQuery Array-like object of UIDs of selected friends.
                */
                return self.getElements().map(function () {
                    return $(this).data('uid');
                });
            },
            createElement: function (uid) {
                /* Construct the HTML node to insert into the message box for a selected friend.
                 */
                return $('<span></span>', {
                    'id': 'recipient-' + uid,
                    'data-uid': uid,
                    'class': 'recipient message_friend_name',
                    'contentEditable': 'False',
                    'text': sharing.allFriends[uid].name
                }).append(
                    $('<span></span>', {
                        'class': 'message_x',
                        'text': 'x'
                    })
                );
            },
            createAddedElement: function (uid) {
                /* Construct the HTML node to insert into the message box for a manually-
                 * selected friend.
                 */
                return $('<div/>', {
                    'id': 'added-' + uid,
                    'data-uid': uid,
                    'class': 'added_friend',
                    'text': sharing.allFriends[uid].name
                }).append(
                    $('<div/>', {
                        'class': 'added_x',
                        'text': 'x'
                    })
                );
            },
            getList: function () {
                var $recipHtmls = self.getElements().map(function () {return this.outerHTML;});
                return commafy($recipHtmls.get());
            },
            reformatList: function () {
                var recipsHtml = self.getList();
                self.getContainerElement().empty().append(recipsHtml);
            },
            cleanUpMessage: function () {
                /* Clean up repeated nbsp, left behind by recipient elements, in the
                 * composed message.
                 */
                var clean = $editable.html().replace(/(&nbsp;){2,}/i, '&nbsp;');
                $editable.html(clean);
            },
            isRecipient: function (uid) {
                /* Return whether the given UID corresponds to a selected friend.
                */
                var recipient = document.getElementById('recipient-' + uid);
                return Boolean(recipient);
            },
            insertElementAtCursor: function (recipientElement) {
                /* Insert selected friend element at cursor position.
                 * A trailing nbsp is required to force the cursor to the correct position.
                 * Upon removing a recipient element, try cleanUpMessage().
                 */
                // Thank you stackoverflow!
                // http://stackoverflow.com/questions/6690752/insert-html-at-cursor-in-a-contenteditable-div
                var sel, range,
                    recipientHTML = recipientElement.get(0).outerHTML + '&nbsp;';

                if (elementContainsSelection($editable.get(0))) {
                    if (window.getSelection) {
                        // IE9 and non-IE
                        sel = window.getSelection();
                        if (sel.getRangeAt && sel.rangeCount) {
                            range = sel.getRangeAt(0);
                            range.deleteContents();

                            // Range.createContextualFragment() would be useful here but is
                            // non-standard and not supported in all browsers (IE9, for one)
                            (function () {
                                var el = document.createElement('div'),
                                    frag = document.createDocumentFragment(), node, lastNode;

                                el.innerHTML = recipientHTML;

                                while (node = el.firstChild) {
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
                            })();
                        }
                    } else if (document.selection && document.selection.type != "Control") {
                        // IE < 9
                        range = document.selection.createRange();
                        range.pasteHTML(recipientHTML);
                    }
                } else {
                    $editable.append(recipientHTML);
                }
            }
        };
        return self;
    })(jQuery, self);

    var buttons = (function ($) {
        /* Methods to advance the active button.
         * (If currently active button is already ahead of requested, it does nothing).
         */
        var classOn = 'button_active',
            classOff = 'button_inactive',
            buttons = [undefined, $('#button_select_all'), $('#button_sugg_msg'), $('#button_do_share')];

        function activateButton (buttons, requestIdx) {
            var currentIdx = 0, activateIdx, i;

            for (i = 1; i < buttons.length; i++) {
                if (buttons[i].hasClass(classOn)) {
                    currentIdx = i;
                }
            }
            activateIdx = Math.max(currentIdx, requestIdx);

            for (i = 1; i < buttons.length; i++) {
                if (i === activateIdx) {
                    buttons[i].removeClass(classOff).addClass(classOn);
                } else {
                    buttons[i].removeClass(classOn).addClass(classOff);
                }
            }
            return activateIdx;
        }

        return {
            activateSuggest: activateButton.bind(this, buttons, 2),
            activateShare: activateButton.bind(this, buttons, 3)
        };
    })(jQuery);

    self.selectFriend = function () {
        /* Register & record friend(s) UI selection
        *
        * Examples:
        *
        *     selectFriend(fbid)
        *     selectFriend(fbid0, fbid1, fbid2)
        *     selectFriend.apply(this, fbids)
        *
        */
        var fbid, element, index, novelIds = [],
            container = self.recipients.getContainerElement();

        for (index in arguments) {
            fbid = arguments[index];
            if (self.recipients.isRecipient(fbid)) {
                continue;
            }

            // If we've used the suggest button, we should have a recips list container,
            // so stick it in there and reformat
            element = self.recipients.createElement(fbid);
            if (container.length > 0) {
                container.append(element);
                self.recipients.reformatList();
            } else { // otherwise, insert at cursor
                self.recipients.insertElementAtCursor(element);
            }

            syncFriendBoxes();  // update the appearance of the friend box
            novelIds.push(fbid);
        }

        if (novelIds.length === 0) {
            // we didn't do anything
            return false;
        }

        buttons.activateSuggest();  // advance the button highlight

        if (edgeflip.faces.debug) {
            var selection_type = 'selected_friend';
            if (novelIds.length === 1 && document.getElementById('wrapper-' + novelIds[0]) === null) 
                selection_type = 'manually_selected_friend';
            edgeflip.events.record(selection_type, {friends: mapFbids(novelIds)});
        }

        $("body").trigger('friendsSelected');
        return true;
    };

    self.unselectFriend = function (fbid) {
        /* when user deselects a friend 
        *
        * activated by unclick a friend to share with or from manual drop or in edit message
        */
        var isSelected = self.recipients.isRecipient(fbid),
            unselection_type;

        if (isSelected) {
            // remove the friend from the message
            $('#recipient-' + fbid).remove();
            syncFriendBoxes();
            self.recipients.cleanUpMessage();
            self.recipients.reformatList();

            if (edgeflip.faces.debug) {
                unselection_type = 'unselected_friend';
                if (document.getElementById('wrapper-' + fbid) === null)
                    unselection_type = 'manually_unselected_friend';

                edgeflip.events.record(unselection_type, {friends: mapFbids([fbid])});
            }
        }
        return isSelected;
    };

    function syncFriendBoxes () {
        // check the friend boxes upstairs first
        $('.friend_box').each(function () {
            var wrapper = this.parentElement,
                $wrapper = $(wrapper),
                uid = $wrapper.data('uid'),
                $this = $(this);

            if (self.recipients.isRecipient(uid)) {
                $this.removeClass('friend_box_unselected').addClass('friend_box_selected');
                $wrapper.find('.xout').hide();
            } else {
                $('#added-' + uid).remove();                  // remove the manually added friend (if it exists)
                $this.removeClass('friend_box_selected').addClass('friend_box_unselected');
                $wrapper.find('.xout').show();
            }
        });

        // go through the manual add friends and make sure they should be there
        $('.added_friend').each(function () {
            var $this = $(this),
                uid = $this.data('uid');

            if (!self.recipients.isRecipient(uid)) {
                $this.remove();
            }
        });

        // finally, if there are any recips without a box, add a manual one
        self.recipients.getUids().each(function () {
            var suggested = $('#friend-' + this).add('#added-' + this);
            if (suggested.length === 0) {
                $('#picked_friends_container').append(self.recipients.createAddedElement(this))
            }
        });
    }

    self.useSuggested = function () {
        /* Populate message container with suggested text.
         */
        edgeflip.events.record('suggest_message_click');

        // grab the pre and post off the front of the queue and stick 'em back on the end
        var msgPair = self.suggestedMessages.shift(),
            msgPre = msgPair[0],
            msgPost = msgPair[1],
            msgNamesContHtml = self.recipients.createContainerElement(),
            recipsHtml, shareButton, difference;
        
        self.suggestedMessages.push(msgPair);

        // If they don't have anyone checked, using the suggested message adds everyone
        if (self.recipients.count() == 0) {
            self.selectAll(true);
        }

        if( msgPre.charAt(msgPre.length - 1) !== '' ) {
            msgPre += ' ';
        }
        
        if( msgPost.charAt(0) !== '' ) {
            msgPost = ' ' + msgPost;
        }
            
        recipsHtml = self.recipients.getList();  // these are going to get blown away, so capture them now
        $editable.empty().append(msgPre, msgNamesContHtml, msgPost);
        self.recipients.getContainerElement().append(recipsHtml);
    
        buttons.activateShare();

        // we don't want to mess with whatever the safari iOS is looking at
        // they could be at any number of zoom levels
        if (!window.navigator.userAgent.match(/(iPad|iPhone)/i)) {
            shareButton = $('#button_do_share', document),
            difference = (shareButton.offset().top + shareButton.outerHeight(true) -
                         $('html,body').scrollTop() + $(window).height());

            //only scroll if share button is below the viewport
            if(difference > 0) {
                $('html,body', document).animate(
                    {scrollTop: '+=' + difference},
                    {duration: 1000}
                );
            }
        }
    };

    /* selects all friends */
    self.selectAll = function (skipRecord) {
        // Have to filter for visible because a friend div might be hidden
        // while awaiting response of an ajax suppression call
        var fbids = [],
            unselected_friend_boxes = $(".friend_box:visible").not(".friend_box_selected"),
            count = self.recipients.count();

        if (!skipRecord) {
            edgeflip.events.record('select_all_click');
        }

        //we want to alert only if there are unselected friend boxes
        //and the count is already at max_face
        unselected_friend_boxes.each(function () {
            var uid;
            if (count === edgeflip.faces.max_face) {
                self.alertTooMany();
                return false;
            }
            uid = $(this.parentElement).data('uid');
            if (!self.recipients.isRecipient(uid)) {
                count++;
                fbids.push(uid);
            }
        });

        $("body").one('friendsSelected', function () {
            //we don't want to mess with whatever the safari iOS is looking at
            //they could be at any number of zoom levels
            if( window.navigator.userAgent.match(/(iPad|iPhone)/i) ) {
            } else {
                $('html,body',document).animate(
                    { scrollTop: $('#button_sugg_msg', document).offset().top - 30 },
                    { duration: 1000 } );
            }
        });

        if (fbids.length) {self.selectFriend.apply(undefined, fbids);}
    };

    /* Tell the user max_face have already been selected */
    self.alertTooMany = function () {
        alert("Sorry: only " + edgeflip.faces.max_face + " friends can be tagged.");
    };

    /* hits facebook API */
    // Called when someone actually shares a message
    self.initShare = function (recursive) {
        var selectAll;

        if (edgeflip.faces.test_mode) {
            alert("Sharing is not allowed in test mode!");
            return;
        }

        if (!recursive) {
            // In case the user is indecisive about publishing, let's only record
            // share_click once.
            edgeflip.events.record('share_click');
        }

        // Quick checks: has the user selected a message and at least one friend with whom to share?
        if (self.recipients.count() === 0) {
            selectAll = confirm("You haven't chosen any friends to share with. \n\n" + 
                                "Click OK to share with all suggested friends or CANCEL to return to the page.");
            if (!selectAll) {
                if (edgeflip.faces.debug) {
                    edgeflip.events.record('empty_share');
                }
                return;
            }
            self.selectAll(true);
        }

        // Request permission to publish story and either publish or re-request
        FB.login(function (response) {
            /* Check that permission to publish has been granted and handle appropriately.
             */
            var authResponse = response.authResponse,
                grantedScopes, permissions, error, publishGranted, doOver;

            if (authResponse !== undefined) {
                grantedScopes = authResponse.grantedScopes;
                if (grantedScopes !== undefined) {
                    permissions = grantedScopes.split(',');
                }
            }

            // Facebook issue
            if (permissions === undefined) {
                // There was an API issue -- record it and barrel forward
                error = JSON.stringify(response);
                edgeflip.events.record('publish_unknown', {
                    content: error.substring(0, 1028),
                    errorMsg: {message: error}
                });
                sendShare();
                return;
            }

            publishGranted = permissions.some(function (permission) {
                return permission === 'publish_actions';
            });

            // Accepted
            if (publishGranted) {
                // All clear, proceed with share
                edgeflip.events.record('publish_accepted'); 
                sendShare();
                return;
            }

            // Denied
            edgeflip.events.record('publish_declined');
            doOver = confirm("Without your permission to publish, we're unable to share this message with your friends. \n\n" +
                             "Click OK to grant permission, or CANCEL to leave the page");
            if (doOver) {
                // Let's try again
                edgeflip.events.record('publish_reminder_accepted');
                self.initShare(true);
                return;
            }

            // Get outta here
            edgeflip.events.record('publish_reminder_declined', {
                complete: edgeflip.util.outgoingRedirect.bind(undefined, edgeflip.faces.errorURL)
            });
        }, {scope: 'publish_actions', return_scopes: true});
    };

    function helperTextDisappear() {
        $('#message_helper_txt').remove();
    }

    function sendShare () {
        helperTextDisappear();
        $('#friends_div').hide();
        $('body').removeClass('faces');
        $('#progress').show();
        $('#progress').removeClass('loading').addClass('sending');
        
        var progressBar = $('#spinner').css('background-image') === 'none',
            progress = 10,
            intervalId;

        if (progressBar) {
            updateProgressBar(progress);
            intervalId = setInterval(
                function() {progress += 10;
                            updateProgressBar(progress);},
                500);
        }

        var recips = self.recipients.getElements().map(function () {
            var $this = $(this),
                uid = $this.data('uid');

            $this.replaceWith("@[" + uid + "]"); // FB mention tag format: @[uid]
            return uid;
        });

        var recipsListContainer = self.recipients.getContainerElement();
        if (recipsListContainer.length > 0) {
            recipsListContainer.replaceWith(recipsListContainer.text());
        }

        var msg = $editable.text().replace(/[\n\r]/g, ' ').substring(0, 1500);

        // Request Facebook share
        var params = {message: msg};
        params[edgeflip.FB_OBJ_TYPE] = edgeflip.FB_OBJ_URL; // required syntax for dynamic property name

        FB.api(
            '/me/' + edgeflip.FB_APP_NAME + ':' + edgeflip.FB_ACTION_TYPE,
            'post',
            params,
            function (response) {
                if (!response || response.error) {
                    // show an alert and then redirect them to wherever the client wants them to go in this case
                    edgeflip.events.record('share_fail', {
                        errorMsg: response.error,
                        complete: function () {
                            alert("Sorry. An error occured sending your message to facebook. Please try again later.");
                            edgeflip.util.outgoingRedirect(edgeflip.faces.errorURL); // set in frame_faces.html
                        }
                    });
                } else {
                    // thank you page redirect happens in recordShare()
                    if (progressBar) {
                        clearInterval(intervalId);
                        if (progress < 70) {updateProgressBar(70);}
                    }
                    recordShare(response.id, msg, recips.get());
                }
            }
        );
    }

    function recordShare(actionid, shareMsg, recips) {
        /* records share event on edgeflip servers; redirects user to thank you page */
        edgeflip.events.record('shared', {
            actionid: actionid,
            friends: mapFbids(recips),
            shareMsg: shareMsg,
            complete: function () {
                updateProgressBar(100);
                // thanksURL set in frame_faces.html
                setTimeout(edgeflip.util.outgoingRedirect.bind(undefined, edgeflip.faces.thanksURL), 500);
            }
        });
    }

    /* set listeners on load */
    $(document)
    .ready(function() {
        /* Event binding & key handling for editable msg div and manually-selected friends.
         */
        var editableLength = $editable.text().length,
            maxEditableLength = 1000;

        // Keys we'll allow even once the message has gotten too long:
        var allowedKeys = [
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
                        ],
            isAllowedKey = function (event) {
                var code = (event.keyCode ? event.keyCode : event.which);
                return allowedKeys.indexOf(code) !== -1;
            },
            isEnterReturn = function (event) {
                var code = (event.keyCode ? event.keyCode : event.which);
                return code == 13 || code == 108;
            };

        $editable
        .on('paste dragover drop', function (event) {
            /* Disable pasting and drag-and-drop to avoid introducing marked-up text.
             */
            event.preventDefault();
        })
        .on('keydown', function (event) {
            /* Prevent enter/return action, and prevent entry of content beyond message
             * length maximum.
             */
            if (isEnterReturn(event) || (editableLength >= maxEditableLength && !isAllowedKey(event))) {
                event.preventDefault();
            } else {
                helperTextDisappear();
                editableLength = $editable.text().length; // sets editableLength for keyup
            }
        })
        .on('keyup', function (event) {
            /* Enforce maximum message length on edit.
             */
            syncFriendBoxes();
            // Doing this here rather than the keydown because the alert seems
            // to cause trouble with the preventDefault() to avoid the input
            if (editableLength >= maxEditableLength && !isAllowedKey(event) && !isEnterReturn(event)) {
                alert("Please limit your message to fewer than " + maxEditableLength + " characters.");
            }
        });

        $editable.add('#picked_friends_container').on('click', '.added_x, .message_x', function () {
            /* X icon next to a friend's name "unselects" the friend.
             */
            var uid = $(this.parentElement).data('uid');
            self.unselectFriend(uid);
        });

    })
    .ready(function () {
        /* Set up the friends faces table and the manual add dropdown
         */
        // use 'on()' delegation to affect dynamically-added elements

        $('#friends_table')
        .on('click', '.friend_box', function () {
            /* Toggle the recipient state of a friend upon checking or unchecking
             */
            var $face = $(this.parentElement),
                uid = $face.data('uid');

            // Try to deselect (and determine if they were selected)
            var deselected = self.unselectFriend(uid),
                alreadySelectedCount;

            if (!deselected) {
                alreadySelectedCount = self.recipients.count();

                if (alreadySelectedCount === edgeflip.faces.max_face) {
                    self.alertTooMany();
                } else {
                    self.selectFriend(uid);
                }
            }
        })
        .on('click', '.xout', function () {
            /* called when someone suppresses a friend (X in faces list)
             * */
            var $face = $(this.parentElement),
                oldUid = $face.data('uid'),
                newUid = self.faceFriends.shift(),
                friend = newUid ? self.allFriends[newUid] : {};

            // Remove the friend from the messages
            self.unselectFriend(oldUid);

            // Hide the suppressed div immediately, because the response to
            // the ajax call can be a little sluggish
            $face.hide();

            // Update the friends shown
            $.ajax({
                type: 'POST',
                url: '/suppress/',
                dataType: 'html',
                data: {
                    userid: edgeflip.faces.user.fbid, // edgeflip.User constructed in frame_faces.html
                    campaignid: edgeflip.faces.campaignid, // campaignid and contentid set in frame_faces.html
                    contentid: edgeflip.faces.contentid,
                    appid: edgeflip.FB_APP_ID,
                    oldid: oldUid,
                    newid: newUid,
                    fname: friend.fname,
                    lname: friend.lname,
                    pic: friend.pic
                },
                error: function () {
                    // Something went wrong, so just remove the div as though no friend was returned
                    $face.remove();
                },
                success: function (data) {
                    if (newUid) {
                        $face.replaceWith(data);
                    } else {
                        // We hid it above, but still need to actually remove it if there's
                        // no new friend coming in (otherwise, a select all will still add this friend)
                        $face.remove();
                    }
                }
            });
        });

        // Buttons //
        // Ensure arguments not interfered with by Event object:
        $('#button_select_all').click(self.selectAll.bind(undefined, false));
        $('#button_sugg_msg').click(self.useSuggested.bind(undefined));
        $('#button_do_share').click(self.initShare.bind(undefined, false));
    }); // document ready

    return self;
})(jQuery, edgeflip);

// This line makes this file show up properly in the Chrome debugger
//# sourceURL=sharing.js
