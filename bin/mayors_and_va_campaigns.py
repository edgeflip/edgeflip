#!/usr/bin/env python

import edgeflip.client_db_tools as cdb
from edgeflip.settings import config


def seedMayorsData():
    """Create a Mayors client and the records associated with initial NV campaign"""
    # Create the client. If a fresh build, this is client_id = 1
    clientId, allFilterId, allChoiceSetId = createMayorsClient()

    # Create the final fallback campaign (anyone). Should be
    # campaign_id = content_id = 1
    fall2CampaignId, fallContentId, fallbackObj = createAllFallback(clientId, allFilterId, allChoiceSetId)

    # Create the first fallback campaign (in Neighbor States). Should be
    # campaign_id = 2 and content_id = 1 (from above)
    fall1CampaignId = createNSFallback(clientId, allFilterId, fallContentId, fallbackObj, fall2CampaignId)

    # Create the main campaign for Nevada; this will have
    # campaign_id = 3 and content_id = 1 (again from above)
    NVCampaignId, contentId = createNVCampaign(clientId, allFilterId, fall1CampaignId, fallContentId)

    print "Mayors Main Campaign ID: %s\nMayors Content ID: %s" % (NVCampaignId, contentId)


def createMayorsClient():
    """Creates the mayors client and default filter and choice set"""
    clientDict = cdb.createClient('Mayors Against Illegal Guns', 'sharing-social-good', '471727162864364', 'edgeflip.com', 'demandaction', True)
    clientId = clientDict.get('client_id')
    allFilterId = clientDict.get('filter_id')
    allChoiceSetId = clientDict.get('choice_set_id')
    return (clientId, allFilterId, allChoiceSetId)


def createAllFallback(clientId, allFilterId, allChoiceSetId):
    """Creates the national fallback for the Mayor's first campaign, returning anyone at all."""
    contentId = cdb.createClientContent(clientId, 'Gun Reform Share into NV', 
        'Fallback Content for the MAIG first targeted sharing campaign.', 
        'http://www.demandaction.org/sandovalsb221?source=fbo_datgsxx0613nssandovts').get('content_id')

    attr = {
        'og_action' : 'support',
        'og_type' : 'cause', 
        'og_title' : 'Tell NV Governor to Sign Background Check Bill',
        'og_image' : 'https://demandaction.edgeflip.com/static/clients/demandaction/mayors_logo.jpg',
        'og_description' : "Ask your friends in NV to tell their Gov: Support Background Checks and Sign SB-221!",
        'page_title' : "Demand Action on Gun Reform",
        'sharing_prompt' : "Ask your Facebook friends to tell Nevada's Governor Sandoval to sign comprehensive background checks into law!",
        'msg1_pre' : "Hey ",
        'msg1_post' : " -- big news! A bill to require background checks for all gun sales just passed the Nevada legislature. Ask your friends in the state to tell their Governor to sign it into law!",
        'msg2_pre' : "Hey ",
        'msg2_post' : " -- big news! A bill to require background checks for all gun sales just passed the Nevada legislature. Ask your friends in the state to tell their Governor to sign it into law!"
    }

    fbObjectId = cdb.createFacebookObject(clientId, 'Gun Reform NV Share Fallback', None, attr).get('fb_object_id')

    campaignId = cdb.createCampaign(clientId, 'MAIG Final Fallback for NV Campaign', None, 
        "http://www.demandaction.org/SandovalSB221Share", 
        "https://donate.demandaction.org/act/donate?source=fbo_datgsxx0613nssandovts", 
        "https://donate.demandaction.org/act/donate?source=fbo_datgsxx0613nssandovts").get('campaign_id')

    cdb.updateCampaignGlobalFilters(campaignId, [(allFilterId, 1.0)])
    cdb.updateCampaignChoiceSets(campaignId, [(allChoiceSetId, 1.0, True, 'all')])

    cdb.updateCampaignFacebookObjects(campaignId, 
        filter_fbObjTupes={allFilterId: [(fbObjectId, 1.0)]}, 
        genericTupes=[(fbObjectId, 1.0)])

    return (campaignId, contentId, fbObjectId)


def createNSFallback(clientId, allFilterId, contentId, fbObjectId, fallbackCampaignId):
    """Creates the first fallback for the Mayor's first campaign, returning anyone in Nevada Neighbor States"""
    statesFilterId = cdb.createFilter(clientId, 'Nevada Border States', None, [('state', 'in', ['California', 'Arizona', 'Utah', 'Idaho', 'Oregon'])]).get('filter_id')
    statesChoiceSetId = cdb.createChoiceSet(clientId, 'In NV Border State', None, [(statesFilterId, 'border', None)]).get('choice_set_id')

    campaignId = cdb.createCampaign(clientId, 'MAIG Border State Fallback for NV Campaign', None, 
        "http://www.demandaction.org/SandovalSB221Share", 
        "https://donate.demandaction.org/act/donate?source=fbo_datgsxx0613nssandovts", 
        "https://donate.demandaction.org/act/donate?source=fbo_datgsxx0613nssandovts",
        fallbackCampaignId, contentId).get('campaign_id')

    cdb.updateCampaignGlobalFilters(campaignId, [(allFilterId, 1.0)])
    cdb.updateCampaignChoiceSets(campaignId, [(statesChoiceSetId, 1.0, True, 'all')])

    cdb.updateCampaignFacebookObjects(campaignId, 
        filter_fbObjTupes={statesFilterId: [(fbObjectId, 1.0)]}, 
        genericTupes=[(fbObjectId, 1.0)])

    return campaignId


def createNVCampaign(clientId, allFilterId, fallbackCampaignId, fallbackContentId):
    """Creates the Mayor's Nevada Campaign"""
    contentId = cdb.createClientContent(clientId, 'NV Gun Reform Call Sandoval', 
        'Main Content for the MAIG first targeted sharing campaign.', 
        'http://www.demandaction.org/sandovalsb221call?source=fbo_datgsxx0613nssandovts').get('content_id')

    filterNV = cdb.createFilter(clientId, 'In Nevada', None, [('state', 'eq', 'Nevada')]).get('filter_id')
    choiceSetNV = cdb.createChoiceSet(clientId, 'In Nevada', None, [(filterNV, 'NV', None)]).get('choice_set_id')

    # Should be the "main" object to actually go to targets in NH
    attr = {
            'og_action' : 'support',
            'og_type' : 'cause', 
            'og_title' : 'Tell NV Governor to Sign Background Check Bill',
            'og_image' : 'https://demandaction.edgeflip.com/static/clients/demandaction/mayors_logo.jpg',
            'og_description' : "Tell NV's Gov: Support Background Checks and Sign SB-221!",
            'page_title' : "Demand Action on Gun Reform",
            'sharing_prompt' : "Ask your Facebook friends in Nevada to tell Governor Sandoval to sign comprehensive background checks into law!",
            'msg1_pre' : "Hey ",
            'msg1_post' : " -- big news! A bill to require background checks for all gun sales just passed the Nevada legislature. Tell Governor Sandoval to sign it into law!",
            'msg2_pre' : "Hey ",
            'msg2_post' : " -- big news! A bill to require background checks for all gun sales just passed the Nevada legislature. Tell Governor Sandoval to sign it into law!"
        }
    objectNV = cdb.createFacebookObject(clientId, 'Gun Reform NV Share', None, attr).get('fb_object_id')

    campaignId = cdb.createCampaign(clientId, 'MAIG NV Campaign', None, 
        "http://www.demandaction.org/SandovalSB221Share", 
        "https://donate.demandaction.org/act/donate?source=fbo_datgsxx0613nssandovts", 
        "https://donate.demandaction.org/act/donate?source=fbo_datgsxx0613nssandovts",
        fallbackCampaignId, fallbackContentId).get('campaign_id')

    cdb.updateCampaignGlobalFilters(campaignId, [(allFilterId, 1.0)])
    cdb.updateCampaignChoiceSets(campaignId, [(choiceSetNV, 1.0, False, None)])

    cdb.updateCampaignFacebookObjects(campaignId, 
        filter_fbObjTupes={ filterNV : [(objectNV, 1.0)] }
        )

    return (campaignId, contentId)



def seedMcAuliffeData():
    """Create the client for VA and the records associated with auth campaigns"""
    # Create the client. If a fresh build, this is client_id = 1
    clientId, allFilterId, allChoiceSetId = createMcAuliffeClient()

    # Create the final fallback campaign (anyone). Should be
    # campaign_id = content_id = 1
    standCampaignId, standingCampaignId, contentId = createAuthVA(clientId, allFilterId, allChoiceSetId)

    print "VA stand Campaign ID: %s\nVA standing Campaign ID: %s\nVA Content ID: %s" % (standCampaignId, standingCampaignId, contentId)

def createMcAuliffeClient():
    """Creates the VA client and default filter and choice set"""
    clientDict = cdb.createClient('Terry McAuliffe for Governor', 'sharing-social-good', '471727162864364', 'edgeflip.com', 'terrymcauliffe', True)
    clientId = clientDict.get('client_id')
    allFilterId = clientDict.get('filter_id')
    allChoiceSetId = clientDict.get('choice_set_id')
    return (clientId, allFilterId, allChoiceSetId)

def createAuthVA(clientId, allFilterId, allChoiceSetId):
    contentId = cdb.createClientContent(clientId, 'McAuliffe VA Auth Campaign Dummy', 
        'Dummy Content for authorization-only buttons (will never be reached).', 
        'https://donate.terrymcauliffe.com/page/contribute/donate').get('content_id')

    standCampaignId = cdb.createCampaign(clientId, 'Auth Campaign for McAuliffe (ver. A)', None, 
        "http://action.terrymcauliffe.com/page/share/stand-with-terry", 
        "https://donate.terrymcauliffe.com/page/contribute/donate", 
        "https://donate.terrymcauliffe.com/page/contribute/donate").get('campaign_id')

    standingCampaignId = cdb.createCampaign(clientId, 'Auth Campaign for McAuliffe (ver. B)', None, 
        "http://action.terrymcauliffe.com/page/share/standing-with-terry", 
        "https://donate.terrymcauliffe.com/page/contribute/donate", 
        "https://donate.terrymcauliffe.com/page/contribute/donate").get('campaign_id')

    return (standCampaignId, standingCampaignId, contentId)


if (__name__ == '__main__'):
    seedMayorsData()
    seedMcAuliffeData() 

    # Should end up with:
    # Mayors NV: https://demandaction.edgeflip.com/button/3/2
    # VA 'Stand': https://terrymcauliffe.edgeflip.com/button/4/3
    # VA 'Standing': https://terrymcauliffe.edgeflip.com/button/5/3

