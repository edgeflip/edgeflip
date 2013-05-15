"""endpoint for demonstrating algo internals.

"""

from .sharing import * # XXX gross

###########################################################################

@app.route('/all_the_dude_ever_wanted')
@app.route('/demo')
@app.route('/button')

@app.route('/rank')
def rank_demo():
    """for demonstration of algo internals to clients
    not user facing
    
    base page - returns HTML container.
    
    originally from demo_flask.py    
    """
    default_users = {
                        'shari': { 'fbid': 1509232539, 'tok': 'AAABlUSrYhfIBAFOpiiSrYlBxIvCgQXMhPPZCUJWM70phLO4gQbssC3APFza3kZCMzlgcMZAkmTjZC9UACIctzDD4pn2ulXkZD'},
                        'rayid': { 'fbid': 500876410, 'tok': 'AAAGtCIn5MuwBAEaZBhZBr1yK6QfUfhgTZBMKzUt9mkapze1pzXYFZAkvBssMoMar0kQ0WTR6psczIkTiU2KUUdduES8tZCrZBfwFlVh3k71gZDZD'},
                        'matt': { 'fbid': 100003222687678, 'tok': 'AAAGtCIn5MuwBAMQ9d0HMAYuHgzSadSNiZAQbGxellczZC1OygQzZBx3vPeStoOhM9j05RmCJhOfcc7OMG4I2pCl2RvdlZCCzAbRNbXic9wZDZD'},
                        '6963': { 'fbid': 6963, 'tok': 'AAAGtCIn5MuwBACC6710Xe3HiUK89U9C9eN58uQPGmfVb83HaQ4ihVvCLAmECtJ0Nttyf3ck59paUirvtZBVZC9kZBMrZCT0ZD'}
                    }

    rank_user = flask.request.args.get('user', '').lower()
    fbid = default_users.get(rank_user, {}).get('fbid', None)
    tok = default_users.get(rank_user, {}).get('tok', None)
    return flask.render_template('rank_demo.html', fbid=fbid, tok=tok)

@app.route('/rank_faces', methods=['POST'])
def rank_faces():
    """for demonstration of algo internals to clients
    not user facing

    AJAX endpoint for two columns of results in rank_demo; returns HTML fragment

    originally from demo_flask.py
    """

    import time
    
    fbid = int(flask.request.json['fbid'])
    tok = flask.request.json['token']
    rankfn = flask.request.json['rankfn']

    if (rankfn.lower() == "px4"):

        # first, spawn a full crawl in the background
        stream_queue.loadQueue(config['queue'], [(fbid, tok, "")])

        # now do a partial crawl real-time
        user = facebook.getUserFb(fbid, tok) # just in case they have no friends
        edgesUnranked = facebook.getFriendEdgesFb(user, tok, requireIncoming=True, requireOutgoing=False)
        edgesRanked = ranking.getFriendRanking(edgesUnranked, requireIncoming=True, requireOutgoing=False)

        # spawn off a separate thread to do the database writing
        database.updateDb(user, tok, edgesRanked, background=True)

    else:
        edgesRanked = ranking.getFriendRankingDb(None, fbid, requireOutgoing=True)

    friendDicts = [ e.toDict() for e in edgesRanked ]

    # Apply control panel targeting filters
    filteredDicts = filter_friends(friendDicts)

    ret = flask.render_template('rank_faces.html', rankfn=rankfn, face_friends=filteredDicts)
    return ret
