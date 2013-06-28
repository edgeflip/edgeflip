#!/usr/bin/env python

import edgeflip.client_db_tools as cdb
from edgeflip.settings import config


def seedClientData():
    """Create a mock client and the records associated with three sample campaigns"""
    # Create the client. If a fresh build, this is client_id = 1
    clientId, allFilterId, allChoiceSetId = createMockClient()

    # Create the guns campaign. If a fresh build, this will have
    # campaign_id = 1 and content_id = 1, which is what we'll set
    # up the mockclient repo to expect. (/guncontrol endpoint)
    createGunsCampaign(clientId, allFilterId, allChoiceSetId)

    # The immigration campaign. Will be campaign_id = content_id = 2
    # in a fresh build. (/immigration endpoint)
    createImmigrationCampaign(clientId, allFilterId, allChoiceSetId)

    # The environment campaign. Will be campaign_id = content_id = 3
    # in a fresh build. (/ofa endpoint)
    createEnviroCampaign(clientId, allFilterId, allChoiceSetId)

    # The McAuliffe campaign. Will be campaign_id = content_id = 4
    # in a fresh build. (/mcauliffe endpoint)
    createMcAuliffeCampaign(clientId, allFilterId, allChoiceSetId)


def createMockClient():
    """Creates the mock clients and default filter and choice set"""
    clientDict = cdb.createClient('mockclient', 'sharing-social-good', '471727162864364', config.web['edgeflip_domain'], config.web['mock_subdomain'], True)
    clientId = clientDict.get('client_id')
    allFilterId = clientDict.get('filter_id')
    allChoiceSetId = clientDict.get('choice_set_id')
    return (clientId, allFilterId, allChoiceSetId)


def createGunsCampaign(clientId, allFilterId, allChoiceSetId):
    """Creates the content and campaign records associated with the mockclient gun control campaign"""
    statesFilterId = cdb.createFilter(clientId, 'Target States', None, [('state', 'in', ['Illinois', 'California', 'Massachusetts', 'New York'])]).get('filter_id')
    statesChoiceSetId = cdb.createChoiceSet(clientId, 'Mayors States', None, [(statesFilterId, 'all', None)]).get('choice_set_id')
    gunsCntId = cdb.createClientContent(clientId, 'Support Gun Control', None, 'http://%s/guncontrol' % config.web['mock_host']).get('content_id')

    mayors_attr = {
        'og_action' : 'support',
        'og_type' : 'cause', 
        'og_title' : 'Gun Control',
        'og_image' : 'http://%s.%s/static/logo.jpg' % (config.web['mock_subdomain'], config.web['edgeflip_domain']),
        'og_description' : "Senators who opposed gun reform have seen their job approval plummet. Check out this infographic to learn more.",
        'page_title' : "Support Gun Control",
        'sharing_prompt' : "Ask your Facebook friends in key states to learn more about gun reform.",
        'msg1_pre' : "Hi there ",
        'msg1_post' : " -- Have you seen this amazing infographic about gun control?",
        'msg2_pre' : "Help keep the pressure on Congress to pass gun control, ",
        'msg2_post' : "!"
    }

    gunsObjId = cdb.createFacebookObject(clientId, 'Gun Control Infographic', None, mayors_attr).get('fb_object_id')

    gunsCmpgId = cdb.createCampaign(clientId, 'Gun Control', None, 
        "http://%s/guncontrol_share" % config.web['mock_host'], 
        "https://donate.demandaction.org/act/donate", 
        "https://donate.demandaction.org/act/donate").get('campaign_id')

    cdb.updateCampaignGlobalFilters(gunsCmpgId, [(allFilterId, 1.0)])
    cdb.updateCampaignChoiceSets(gunsCmpgId, [(statesChoiceSetId, 1.0, True, 'all')])

    cdb.updateCampaignFacebookObjects(gunsCmpgId, 
        filter_fbObjTupes={statesFilterId: [(gunsObjId, 1.0)]}, 
        genericTupes=[(gunsObjId, 1.0)])


def createImmigrationCampaign(clientId, allFilterId, allChoiceSetId):
    """Creates the content and campaign records associated with the mockclient immigration campaign"""
    immgCntId = cdb.createClientContent(clientId, 'Support Immigration Reform', None, 'http://%s/immigration' % config.web['mock_host']).get('content_id')

    obama_attr = {
        'og_action' : 'support',
        'og_type' : 'cause', 
        'og_title' : 'Immigration Reform',
        'og_image' : 'http://%s.%s/static/logo.jpg' % (config.web['mock_subdomain'], config.web['edgeflip_domain']),
        'og_description' : "President Obama supports common sense reforms to fix our broken immigration system. Learn more and show your support.",
        'page_title' : "Support Immigration Reform",
        'sharing_prompt' : "Ask your Facebook friends to learn more about immigration reform.",
        'msg1_pre' : "Hi there ",
        'msg1_post' : " -- Check out these details about the President's blueprint for immigration reform.",
        'msg2_pre' : "Help keep the pressure on Congress to pass immigration reform, ",
        'msg2_post' : "!"
    }

    immgObjId = cdb.createFacebookObject(clientId, 'Immigration Reform Blueprint', None, obama_attr).get('fb_object_id')

    immgCmpgId = cdb.createCampaign(clientId, 'Immigration Reform', None, 
        "http://%s/immigration_share" % config.web['mock_host'], 
        "https://contribute.barackobama.com/donation/orgforaction/2/index.html", 
        "https://contribute.barackobama.com/donation/orgforaction/2/index.html").get('campaign_id')

    cdb.updateCampaignGlobalFilters(immgCmpgId, [(allFilterId, 1.0)])
    cdb.updateCampaignChoiceSets(immgCmpgId, [(allChoiceSetId, 1.0, True, 'all')])

    cdb.updateCampaignFacebookObjects(immgCmpgId, 
        filter_fbObjTupes={allFilterId: [(immgObjId, 1.0)]}, 
        genericTupes=[(immgObjId, 1.0)])


def createEnviroCampaign(clientId, allFilterId, allChoiceSetId):
    """Creates the content and campaign records associated with the mockclient OFA-skinned environment campaign"""
    filterIL = cdb.createFilter(clientId, 'In Illinois', None, [('state', 'eq', 'Illinois')]).get('filter_id')
    filterMA = cdb.createFilter(clientId, 'In Massachusetts', None, [('state', 'eq', 'Massachusetts')]).get('filter_id')
    filterCA = cdb.createFilter(clientId, 'In California', None, [('state', 'eq', 'California')]).get('filter_id')
    filterNY = cdb.createFilter(clientId, 'In New York', None, [('state', 'eq', 'New York')]).get('filter_id')

    ofaChoiceSet = cdb.createChoiceSet(clientId, 'OFA Enviro States', None, 
                    [(filterIL, 'IL', None), (filterMA, 'MA', None), (filterCA, 'CA', None), (filterNY, 'NY', None)]).get('choice_set_id')

    ofaContent = cdb.createClientContent(clientId, 'OFA Enviro pages', None, 'http://%s/ofa_landing?state={{choice_set_slug}}' % config.web['mock_host']).get('content_id')

    attr = lambda sen,st: {
            'og_action' : 'support',
            'og_type' : 'cause', 
            'og_title' : 'Climate Legislation',
            'og_image' : 'http://%s.%s/static/logo.jpg' % (config.web['mock_subdomain'], config.web['edgeflip_domain']),
            'og_description' : "The time has come for real climate legislation in America. Tell Senator %s that you stand with President Obama and Organizing for Action on this important issue." % (sen),
            'page_title' : "Tell Sen. %s We're Putting Denial on Trial!" % (sen),
            'sharing_prompt' : "Ask your Facebook friends in %s to let Senator %s know we're putting climate denial on trial!" % (st, sen),
            'msg1_pre' : "Hi there ",
            'msg1_post' : " -- Contact Sen. %s to say you stand with the president on climate legislation!" % (sen),
            'msg2_pre' : "Now is the time for real climate legislation, ",
            'msg2_post' : "!"
        }
    objectIL = cdb.createFacebookObject(clientId, 'OFA Enviro - IL', None, attr("Rowlf the Dog", "Illinois")).get('fb_object_id')
    objectMA = cdb.createFacebookObject(clientId, 'OFA Enviro - MA', None, attr("Kermit the Frog", "Massachusetts")).get('fb_object_id')
    objectCA = cdb.createFacebookObject(clientId, 'OFA Enviro - CA', None, attr("Fozzie Bear", "California")).get('fb_object_id')
    objectNY = cdb.createFacebookObject(clientId, 'OFA Enviro - NY', None, attr("Miss Piggy", "New York")).get('fb_object_id')

    generic_attr = {
            'og_action' : 'support',
            'og_type' : 'cause', 
            'og_title' : 'Climate Legislation',
            'og_image' : 'http://%s.%s/static/logo.jpg' % (config.web['mock_subdomain'], config.web['edgeflip_domain']),
            'og_description' : "The time has come for real climate legislation in America. Tell your Senator that you stand with President Obama and Organizing for Action on this important issue.",
            'page_title' : "Tell your Senator We're Putting Denial on Trial!",
            'sharing_prompt' : "Ask your Facebook friends to let their Senators know we're putting climate denial on trial!",
            'msg1_pre' : "Hi there ",
            'msg1_post' : " -- Contact your Senator to say you stand with the president on climate legislation!",
            'msg2_pre' : "Now is the time for real climate legislation, ",
            'msg2_post' : "!"
        }
    objectGen = cdb.createFacebookObject(clientId, 'OFA Enviro - Generic', None, generic_attr).get('fb_object_id')


    ofaCmpgId = cdb.createCampaign(clientId, 'OFA Enviro Support', None, 
        "http://%s/ofa_share" % config.web['mock_host'], 
        "https://contribute.barackobama.com/donation/orgforaction/2/index.html", 
        "https://contribute.barackobama.com/donation/orgforaction/2/index.html").get('campaign_id')

    cdb.updateCampaignGlobalFilters(ofaCmpgId, [(allFilterId, 1.0)])
    cdb.updateCampaignChoiceSets(ofaCmpgId, [(ofaChoiceSet, 1.0, True, 'all')])

    cdb.updateCampaignFacebookObjects(ofaCmpgId, 
        filter_fbObjTupes={ filterIL : [(objectIL, 1.0)], 
                            filterMA : [(objectMA, 1.0)], 
                            filterCA : [(objectCA, 1.0)], 
                            filterNY : [(objectNY,1.0)]
                        }, 
        genericTupes=[(objectGen,1.0)])


def createMcAuliffeCampaign(clientId, allFilterId, allChoiceSetId):
    """Creates the content and campaign records associated with the mockclient mcauliffe campaign"""
    statesFilterId = cdb.createFilter(clientId, 'In Virginia', None, [('state', 'eq', 'Virginia')]).get('filter_id')
    statesChoiceSetId = cdb.createChoiceSet(clientId, 'In Virginia', None, [(statesFilterId, 'all', None)]).get('choice_set_id')
    vaCntId = cdb.createClientContent(clientId, 'Support Terry McAuliffe', None, 'http://%s/mcauliffe' % config.web['mock_host']).get('content_id')
    vaStyleId = cdb.createButtonStyle(clientId, 'VA Share Button', None, htmlFile='clients/terrymcauliffe/share_button.html').get('button_style_id')

    va_attr = {
        'og_action' : 'support',
        'og_type' : 'cause', 
        'og_title' : 'Terry McAuliffe for Governor',
        'og_image' : 'http://action.terrymcauliffe.com/page/-/targetedsharing/targetedsharign_thumb.png',
        'og_description' : """Terry McAuliffe supports access to safe and legal abortion, while the Washington Post writes that Ken Cuccinelli is waging a "War on Abortion." Learn more about your choices for Governor.""",
        'page_title' : "Support Terry McAuliffe for Governor",
        'sharing_prompt' : "There's a Clear Choice in this Election. If You Want a Governor who Stands Up for Women's Rights, Spread the Word to Your Friends on Facebook:",
        'msg1_pre' : "Hey, ",
        'msg1_post' : ", do you know about the candidates running for Governor in Virginia? Learn more about their positions on women's rights and decide for yourself.",
        'msg2_pre' : "Did you hear the latest from the Virginia Governor's Race ",
        'msg2_post' : "? There's a clear choice when it comes to their positions on women's right: Terry McAuliffe"
    }

    vaObjId = cdb.createFacebookObject(clientId, 'McAuliffe Infographic', None, va_attr).get('fb_object_id')

    vaCmpgId = cdb.createCampaign(clientId, 'McAuliffe for Governor', None, 
        "http://%s/mcauliffe_share" % config.web['mock_host'], 
        "https://donate.terrymcauliffe.com/page/contribute/thanks-donate", 
        "https://donate.terrymcauliffe.com/page/contribute/thanks-donate").get('campaign_id')

    cdb.updateCampaignGlobalFilters(vaCmpgId, [(allFilterId, 1.0)])
    cdb.updateCampaignChoiceSets(vaCmpgId, [(statesChoiceSetId, 1.0, True, 'all')])
    cdb.updateCampaignButtonStyles(vaCmpgId, [(vaStyleId, 1.0)])

    cdb.updateCampaignFacebookObjects(vaCmpgId, 
        filter_fbObjTupes={statesFilterId: [(vaObjId, 1.0)]}, 
        genericTupes=[(vaObjId, 1.0)])



if (__name__ == '__main__'):
    seedClientData()    

