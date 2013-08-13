#!/usr/bin/env python
import argparse
import sys
import edgeflip.client_db_tools as cdb
from edgeflip.settings import config

import edgeflip.database as db



CLIENT_NAME = "Edgeflip Test"
FB_APP_ID = 526715140728525
FB_APP_NAME = "edgeflip-local"
CLIENT_URL = "http://rattigan.org"



conn = db.getConn()
curs = conn.cursor()

def getClientIdFromName(clientName):
    curs.execute("SELECT client_id FROM clients WHERE name=%s", (clientName,))
    return curs.fetchone()[0] if (curs.rowcount) else None
def getCampaigns(clientId):
    curs.execute("SELECT campaign_id FROM campaigns WHERE client_id=%s", (clientId,))
    return [ r[0] for r in curs.fetchall() ]
def getContents(clientId):
    curs.execute("SELECT content_id FROM client_content WHERE client_id=%s", (clientId,))
    return [ r[0] for r in curs.fetchall() ]


####################################################

if (__name__ == '__main__'):

    parser = argparse.ArgumentParser(description='Run a devel server from localhost')
    parser.add_argument('--client-name', default=CLIENT_NAME, help='name for the test client')
    parser.add_argument('--app-id', default=FB_APP_ID, help='fb app id')
    parser.add_argument('--app-name', default=FB_APP_NAME, help='fb app name')
    parser.add_argument('--client-url', default=CLIENT_URL, help='url of client')
    args = parser.parse_args()


    clientId = getClientIdFromName(args.client_name)
    clientAppUrls = []
    if (clientId is not None):
        for campaignId in getCampaigns(clientId):
            for contentId in getContents(clientId):
                # https://apps.facebook.com/edgeflip-local/10/11
                clientAppUrls.append("https://apps.facebook.com/%s/%d/%d" % (args.app_name, campaignId, contentId))

    else:
        clientDict = cdb.createClient(args.client_name, args.app_name, args.app_id, None, None, True)
        clientId = clientDict.get('client_id')
        allFilterId = clientDict.get('filter_id')
        allChoiceSetId = clientDict.get('choice_set_id')
        contentId = cdb.createClientContent(clientId, None, None, args.client_url).get('content_id')

        attrs = {
            'og_action' : 'support',
            'og_type' : 'cause',
            'og_title' : args.client_name,
            'og_image' : 'https://edgeflip.fwd.wf/static/logo.jpg',
            'og_description' : "This is a test.",
            'page_title' : "Testing",
            'sharing_prompt' : "Share some stuff for fun and profit",
            'msg1_pre' : "Hi there ",
            'msg1_post' : " -- check this out (you know you want to).",
            'msg2_pre' : "Hi there ",
            'msg2_post' : " -- check this out (or not).",
        }
        objectId = cdb.createFacebookObject(clientId, 'test content', None, attrs).get('fb_object_id')

        campaignId = cdb.createCampaign(clientId, args.client_name + " test", None,
            "http://%s/guncontrol_share" % config.web['mock_host'],
            "http://edgeflip.com/thanks",
            "http://edgeflip.com/error").get('campaign_id')
        cdb.updateCampaignGlobalFilters(campaignId, [(allFilterId, 1.0)])
        cdb.updateCampaignChoiceSets(campaignId, [(allChoiceSetId, 1.0, True, 'all')])

        cdb.updateCampaignFacebookObjects(campaignId,
            filter_fbObjTupes={allFilterId: [(objectId, 1.0)]},
            genericTupes=[(objectId, 1.0)])


        clientAppUrls.append("https://apps.facebook.com/%s/%d/%d" % (args.app_name, campaignId, contentId))

    sys.stdout.write("\nclient #%d %s: \n" % (clientId, args.client_name))
    for url in clientAppUrls:
        sys.stdout.write("\t" + url + "\n")
