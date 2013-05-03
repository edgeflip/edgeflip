"""code for testing/benchmarking endpoints

XXX This can probably die

"""

from .ofa_flask import * # XXX gross

# Endpoint for testing a faces response...
# (might just want to ultimately do this inline by passing a test mode param so we can actually spin up threads, etc.)
@app.route("/face_test", methods=['GET','POST'])
def face_test():
    """webserver (flask + apache) benchmark method. fakes facebook, can probably die.

    """
    maxTime = int(flask.request.args.get('maxtime', 7))

    # Simulate taking to facebook with a 0-7 second sleep
    s = random.randint(0,maxTime)
    time.sleep(s)

    # Generate between 50 and 450 fake friend edges
    fc = random.randint(50,650)
    edgesUnranked = []
    for i in range(fc):

        muts = random.randint(0,25)
        primPhoto = random.randint(0,10)
        otherPhoto = random.randint(0,20)

        edgesUnranked.append(
            datastructs.Edge(
                datastructs.UserInfo(500876410, 'Rayid', 'Ghani', 'male', datetime.date(1975,03,14), 'Chicago', 'Illinois'),
                datastructs.FriendInfo(500876410, 6963, 'Bob', 'Newhart', 'male', datetime.date(1930,01,01), 'Chicago', 'Illinois', primPhoto, otherPhoto, muts),
                random.randint(0,10), random.randint(0,5), random.randint(0,3), random.randint(0,3), random.randint(0,7), random.randint(0,3), random.randint(0,5),
                random.randint(0,10), random.randint(0,5), random.randint(0,3), random.randint(0,3), random.randint(0,7), random.randint(0,3), random.randint(0,5),
                primPhoto, otherPhoto, muts
            )

        )


    # Actually rank these edges and generate friend dictionaries from them
    edgesRanked = ranking.getFriendRanking(500876410, edgesUnranked, requireOutgoing=False)

    campaign_filterTups = config.ofa_campaigns
    campaign = "test"
    filterTups = campaign_filterTups.get(campaign, [])
    edgesFiltered = filterEdgesBySec(edgesRanked, filterTups)

    friendDicts = [ e.toDict() for e in edgesFiltered ]
    faceFriends = friendDicts[:6]
    numFace = len(faceFriends)
    allFriends = friendDicts[:25]

    # zzz state = target state with most friends
    state = 'EC'

    targetDict = state_senInfo.get(state)

    msgParams = {
    'msg1_pre' : "Hi there ",
    'msg1_post' : " -- Contact Sen. %s to say you stand with the president on climate legislation!" % targetDict['name'],
    'msg2_pre' : "Now is the time for real climate legislation, ",
    'msg2_post' : "!",
    'msg_other_prompt' : "Checking friends on the left will add tags for them (type around their names):",
    'msg_other_init' : "Replace this text with your message for "
    }

    actionParams =     {
    'fb_action_type' : 'support',
    'fb_object_type' : 'cause',
    'fb_object_url' : 'http://demo.edgeflip.com/ofa_climate/%s' % state
    }
    actionParams.update(fbParams)

    return flask.render_template('ofa_faces_table.html', fbParams=actionParams, msgParams=msgParams, senInfo=targetDict,
                                 face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace)
