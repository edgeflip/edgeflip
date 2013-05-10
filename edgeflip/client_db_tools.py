
# Eventually this module should serve as the backing for a control panel API

# Will generally need to work out some auth, probably at the API level
# (including a check that requests are always consistent with the authed user)


import time
import random
import logging
import threading
from MySQLdb import IntegrityError

from . import database as db
from . import datastructs
from .settings import config 

logger = logging.getLogger(__name__)

"""TODO: verify client_id matches between object & campaign when creating associations!"""

FILTER_LIST_DELIM = '||'  # Shouldn't move to config, since this needs to be globally used in the DB


def createClient(name, fbAppName, fbAppId, domain, subdomain, generateDefaults=False):
    """Creates a new client in the database, returning the client_id.
    Optionally, creates default objects that can be used to get up and
    running more quickly.
    """

    row = {
            'name' : name, 
            'fb_app_name' : fbAppName, 
            'fb_app_id' : fbAppId, 
            'domain' : domain, 
            'subdomain' : subdomain 
          }

    try:
        clientId = dbInsert('clients', 'client_id', row.keys(), [row])
    except IntegrityError as e:
        return {'error' : str(e)}

    ret = {'client_id' : clientId}

    if (generateDefaults):
        defaultName = 'edgeflip default'
        defaultDesc = 'Default element created by edgeflip'

#        buttonStyleId = createButtonStyle(clientId, defaultName, defaultDesc, 'ef_default_button.html', 'ef_default_button.css').get('button_style_id')
#        facesStyleId = createFacesStyle(clientId, defaultName, defaultDesc, 'ef_default_faces.html', 'ef_default_faces.css').get('faces_style_id')

        # zzz best way to get default propensity, proximity, and mix model id's (and choice set algorithms) that are created globally?

        filterId = createFilter(clientId, defaultName, defaultDesc).get('filter_id')
        choiceSetId = createChoiceSet(clientId, defaultName, defaultDesc, [(filterId, 'all', None)]).get('choice_set_id')

        row = {
                'client_id' : clientId, 
                'filter_id' : filterId, 
                'choice_set_id' : choiceSetId
              }

        clientDefaultId = dbInsert('client_defaults', 'client_default_id', row.keys(), [row], 'client_id', clientId, replaceAll=True)

        ret['filter_id'] = filterId
        ret['choice_set_id'] = choiceSetId
        ret['client_default_id'] = clientDefaultId

    return ret


def validateClientSubdomain(campaignId, contentId, clientSubdomain):
    """Utility function to check that the client_id associated with
    a given campaign_id and content_id match the subdomain that the
    request came in on."""
    cmpgClientId = dbGetObject('campaigns', ['client_id'], 'campaign_id', campaignId)[0][0]
    cntClientId = dbGetObject('client_content', ['client_id'], 'content_id', contentId)[0][0]

    if (cmpgClientId != cntClientId):
        logging.error("Campaign and content must belong to the same client")
        raise ValueError("Campaign and content must belong to the same client")

    sub = dbGetClient(cmpgClientId, ['subdomain'])[0][0]

    if (sub != clientSubdomain):
        logging.error("Subdomain must match campaign's client_id")
        raise ValueError("Subdomain must match campaign's client_id")

    return cmpgClientId


def createButtonStyle(clientId, name, description, htmlFile, cssFile):
    """Right now, button styles are hard-coded in the app."""
    raise NotImplementedError

def createFacesStyle(clientId, name, description, htmlFile, cssFile):
    """Right now, faces styles are hard-coded in the app."""
    raise NotImplementedError

def createFilter(clientId, name, description, features=None, metadata=None):
    """Creates a new filter associated with the given client

    features should be a list of tupes of the form: (feature, operator, value)
    """

    features = features if (features is not None) else []
    metadata = metadata if (metadata is not None) else []

    row = {
            'client_id' : clientId, 
            'name' : name, 
            'description' : description
          }

    # zzz This will create the filter record, commit, then load the features & meta data
    #     would we rather the commit only happen if everything gets in?
    try:
        filterId = dbInsert('filters', 'filter_id', row.keys(), [row])
    except IntegrityError as e:
        return {'error' : str(e)}

    updateFilterFeatures(filterId, features, replaceAll=True)
    updateMetadata('filter_meta', 'filter_meta_id', 'filter_id', filterId, metadata, replaceAll=True)

    return {'filter_id' : filterId}

def updateFilterFeatures(filterId, features, replaceAll=False):
    """Update features that define a filter

    features should be a list of tupes of the form: (feature, operator, value)
    """

    if (not features):
        return 0    # no records to insert

    rows = []
    newFeatures = []
    for feature, operator, value in features:
        if (isinstance(value, int) or isinstance(value, long)):
            value_type = 'int'
        elif isinstance(value, float):
            value_type = 'float'
            value = '%.8f' % value
        elif isinstance(value, str):
            value_type = 'string'
        elif isinstance(value, list):
            value_type = 'list'
            value = FILTER_LIST_DELIM.join([str(v) for v in value])
        else:
            raise ValueError("Can't filter on type of %s" % value)

        # Check if we're trying to insert the same 
        # feature/operator combo more than once
        if ((feature, operator) in newFeatures):
            raise ValueError("Filter features must be unique on feature & operator. Duplicate found for (%s, %s)" % (feature, operator))

        newFeatures.append((feature, operator))
        rows.append({
                    'filter_id' : filterId, 
                    'feature' : feature, 
                    'operator' : operator, 
                    'value' : str(value), 
                    'value_type' : value_type
                    })

    insCols = ['filter_id', 'feature', 'operator', 'value', 'value_type']
    uniqueCols = ['feature', 'operator']

    dbInsert('filter_features', 'filter_feature_id', insCols, rows, 'filter_id', filterId, uniqueCols, replaceAll=replaceAll)

    return len(rows)


def updateCampaignGlobalFilters(campaignId, filterTupes):
    """Associate filters with a campaign.
    Will always replace all rows associated with this campaign in the table,
    since any change affects ALL probabilities.

    filterTupes should be (filter_id, CDF probability)
    """

    # Ensure the CDF described by these tuples is well-defined
    # before trying to insert them (this will raise an exception if not)
    checkCDF(filterTupes)

    rows = []
    for filterId, prob in filterTupes:
        rows.append({
                    'campaign_id' : campaignId,
                    'filter_id' : filterId,
                    'rand_cdf' : prob
                    })

    insCols = ['campaign_id', 'filter_id', 'rand_cdf']

    dbInsert('campaign_global_filters', 'campaign_global_filter_id', insCols, rows, 'campaign_id', campaignId, replaceAll=True)

    return len(rows)


def getFilter(filterId):
    """Reads a filter from the database and returns a Filter object"""

    rows = dbGetObjectAttributes('filter_features', ['feature', 'operator', 'value', 'value_type'], 
                                'filter_id', filterId)

    features = []
    for feature, operator, value, value_type in rows:
        if value_type == 'int':
            value = int(value)
        elif value_type == 'float':
            value = float(value)
        elif value_type == 'string':
            value = str(value)
        elif value_type == 'list':
            value = value.split(FILTER_LIST_DELIM)
        else:
            raise ValueError("Unknown filter value type: %s" % value_type)

        features.append((feature, operator, value))

    return Filter(filterId, features)


def createChoiceSet(clientId, name, description, filters, metadata=None):
    """Create a new choice set associated with this client

    filters is a list of tuples of the form: (filterId, urlSlug, modelType)
    """

    if (not filters):
        raise ValueError("Must associate at least one filter with a choice set")
    metadata = metadata if (metadata is not None) else []

    row = {
            'client_id' : clientId,
            'name' : name,
            'description' : description
          }

    try:
        choiceSetId = dbInsert('choice_sets', 'choice_set_id', row.keys(), [row])
    except IntegrityError as e:
        return {'error' : str(e)}

    updateChoiceSetFilters(choiceSetId, filters, replaceAll=True)
    updateMetadata('choice_set_meta', 'choice_set_meta_id', 'choice_set_id', choiceSetId, metadata, replaceAll=True)

    return {'choice_set_id' : choiceSetId}


def updateChoiceSetFilters(choiceSetId, filters, replaceAll=False):
    """Update the filters that make up a given choice set, Optionally
    replacing all of the current filters or adding to the existing
    definition (note that records for filters already associated with
    the choice set and passed here in the filters list will be replaced 
    in either case).

    filters should be a list of tuples of form: (filterId, urlSlug, modelType)
    """

    if (not filters):
        return 0    # no records to insert

    rows = []
    newFilters = []
    for filterId, urlSlug, modelType in filters:

        # Check if we're trying to insert the same filter more than once
        if (filterId in newFilters):
            raise ValueError("Choice set filters must be unique. Duplicate found for %s" % filterId)

        newFilters.append(filterId)
        rows.append({
                    'choice_set_id' : choiceSetId, 
                    'filter_id' : filterId, 
                    'url_slug' : urlSlug,
                    'propensity_model_type' : modelType
                    })

    insCols = ['choice_set_id', 'filter_id', 'url_slug', 'propensity_model_type']
    uniqueCols = ['filter_id']

    dbInsert('choice_set_filters', 'choice_set_filter_id', insCols, rows, 'choice_set_id', choiceSetId, uniqueCols, replaceAll=replaceAll)

    return len(rows)


def updateCampaignChoiceSets(campaignId, choiceSetTupes):
    """Update the choice sets associated with a campaign.
    Will always replace all rows associated with this campaign in the table,
    since any change affects ALL probabilities

    choiceSetTupes should be (choice_set_id, CDF probability, allowGeneric, genericSlug)
    In the tuples:
        allowGeneric is a boolean to specify whether the campaign should fall back to
          generic content if too few friends fall in a given choice set filter.
        genericSlug provides the url slug that should be passed through to the content URL
          in that case. 
    """
    checkCDF([t[:2] for t in choiceSetTupes])

    rows = []
    for choiceSetId, prob, allowGeneric, genericSlug in choiceSetTupes:
        rows.append({
                    'campaign_id' : campaignId,
                    'choice_set_id' : choiceSetId,
                    'rand_cdf' : prob,
                    'allow_generic' : allowGeneric,
                    'generic_url_slug' : genericSlug
                    })

    insCols = ['campaign_id', 'choice_set_id', 'rand_cdf', 'allow_generic', 'generic_url_slug']

    dbInsert('campaign_choice_sets', 'campaign_choice_set_id', insCols, rows, 'campaign_id', campaignId, replaceAll=True)

    return len(rows)


def getChoiceSet(choiceSetId):
    """Reads a choice set from database and returns a ChoiceSet object."""

    rows = dbGetObjectAttributes('choice_set_filters', ['choice_set_filter_id', 'filter_id', 'url_slug', 'propensity_model_type'], 
                                'choice_set_id', choiceSetId)
    csFilters = [ChoiceSetFilter(r[0], r[1], r[2], r[3], filterObj=getFilter(r[1])) for r in rows]
    return ChoiceSet(choiceSetId, csFilters)


def createClientContent(clientId, name, description, url):
    """Create an entry for a piece of content on a client's server.
    This will be used to determine where to send users after they
    clickback off a share on Facebook.

    url may contain {{choice_set_slug}} and {{fb_object_slug}} to allow
    for templating of parameters to tell the client server what page to
    display to the user on their side.
    """
    if (not url):
        raise ValueError("Must provide a URL")

    row = {
            'client_id' : clientId,
            'name' : name,
            'description' : description,
            'url' : url
          }

    try:
        clientContentId = dbInsert('client_content', 'client_content_id', row.keys(), [row])
    except IntegrityError as e:
        return {'error' : str(e)}

    return {'client_content_id' : clientContentId}


def getClientContentURL(contentId, choiceSetFilterSlug, fbObjectSlug):
    """Return a URL for a piece of client content, with choice set and
    facebook object slugs filled in.
    """
    choiceSetFilterSlug = choiceSetFilterSlug or ''
    fbObjectSlug = fbObjectSlug or ''

    sql = "SELECT url FROM client_content WHERE content_id = %s" % contentId
    conn = db.getConn()
    curs = conn.cursor()

    try:
        curs.execute(sql)
        url = curs.fetchone()[0]
    finally:
        conn.close()

    # Fill in choice set and FB object slugs
    url = url.replace('{{choice_set_slug}}', choiceSetFilterSlug)
    url = url.replace('{{fb_obj_slug}}', fbObjectSlug)

    return url


def createCampaign(clientId, name, description, facesURL, fallbackCampaign=None, fallbackContent=None, metadata=None):
    """Create a new campaign associated with the given client.

    facesURL must be provided and specifies the page on the client's servers
    that will hold the iframe with the facces/message for sharing.
    Specifying a fallback campaign and content are optional, but can be used
    to allow for trying a second campaign if we don't have friends to return
    for the current one.
    """
    if (not facesURL):
        raise ValueError("Must specify a URL for the faces page")
    metadata = metadata if (metadata is not None) else []

    row = {
            'client_id' : clientId,
            'name' : name,
            'description' : description
          }

    try:
        campaignId = dbInsert('campaigns', 'campaign_id', row.keys(), [row])
    except IntegrityError as e:
        return {'error' : str(e)}

    updateCampaignProperties(campaignId, facesURL, fallbackCampaign, fallbackContent)
    updateMetadata('campaign_meta', 'campaign_meta_id', 'campaign_id', campaignId, metadata, replaceAll=True)

    return {'campaign_id' : campaignId}


def updateCampaignProperties(campaignId, facesURL, fallbackCampaign=None, fallbackContent=None):
    """Update the properties associated with a given campaign."""
    if (not facesURL):
        raise ValueError("Must specify a URL for the faces page")

    row = {
            'campaign_id' : campaignId,
            'client_faces_url' : facesURL,
            'fallback_campaign_id' : fallbackCampaign,
            'fallback_content_id' : fallbackContent
          }

    dbInsert('campaign_properties', 'campaign_property_id', row.keys(), [row], 'campaign_id', campaignId, replaceAll=True)

    return 1


def getFacesURL(campaignId, contentId):
    """Get the URL (on the client's servers) for the page that will hold
    the faces iframe. Add querystring parameters for the campaign_id and
    content_id that our faces page will have to pick up...
    """
    url = dbGetObjectAttributes('campaign_properties', ['client_faces_url'], 'campaign_id', campaignId)[0][0]
    if (url.find('?') == -1):
        url += '?'
    else:
        url += '&'
    
    return url + 'efcmpg=' + str(campaignId) + '&efcnt=' + str(contentId)


def checkRequiredFbObjAttributes(attributes):
    """Helper function to check that an atrribute dictionary being used to
    define a Facebook object contains all the required pieces of information.
    """
    required_attributes = ['og_action', 'og_type', 'og_title', 'og_image', 'og_description', 'sharing_prompt']
    for attr in required_attributes:
        if (not attributes.get(attr)):
            raise ValueError("Must specify %s for the Facebook object." % attr)


def createFacebookObject(clientId, name, description, attributes, metadata=None):
    """Create a new Facebook object associated with the client. This determines
    both what will actually be shared on facebook and the prompt & suggested
    messages for our sharing page (since those should relate to each other)

    attributes is a dictionary of the various attributes of the object, too
    numerous to include as separate parameters to the function."""

    checkRequiredFbObjAttributes(attributes)
    metadata = metadata if (metadata is not None) else []

    row = {
            'client_id' : clientId,
            'name' : name,
            'description' : description
          }

    try:
        fbObjectId = dbInsert('fb_objects', 'fb_object_id', row.keys(), [row])
    except IntegrityError as e:
        return {'error' : str(e)}

    updateFacebookObjectAttributes(fbObjectId, attributes)
    updateMetadata('fb_object_meta', 'fb_object_meta_id', 'fb_object_id', fbObjectId, metadata, replaceAll=True)

    return {'fb_object_id' : fbObjectId}


def updateFacebookObjectAttributes(fbObjectId, attributes):
    """Update the attributes associated with an existing Facebook object"""
    checkRequiredFbObjAttributes(attributes)

    row = attributes
    row['fb_object_id'] = fbObjectId

    dbInsert('fb_object_attributes', 'fb_object_attributes_id', row.keys(), [row], 'fb_object_id', fbObjectId, replaceAll=True)

    return 1


def updateCampaignFacebookObjects(campaignId, filter_fbObjTupes=None, genericTupes=None):
    """Update the facebook objects associated with a given campaign.
    Will always replace all rows associated with this campaign in the table,
    since any change affects ALL probabilities

    filter_fbObjTupes should be a dictionary: {filter_id : [(fb_object_id, CDF Prob)]}
    
    TODO: Should probably include check against DB to ensure objects are provided for 
          ALL choice set filters that have been associated with the campaign 
          (otherwise, someone could come in, get assigned to a set of friends, but have
          no facebook object to share with them!)
    """
    for filterId, tupes in filter_fbObjTupes.items():
        checkCDF(tupes)
    if (genericTupes):
        checkCDF(genericTupes)

    numRows = 0

    if (filter_fbObjTupes):
        filter_rows = []
        for filterId, tupes in filter_fbObjTupes.items():
            for fbObjectId, prob in tupes:
                filter_rows.append({
                            'campaign_id' : campaignId,
                            'filter_id' : filterId,
                            'fb_object_id' : fbObjectId,
                            'rand_cdf' : prob
                            })

        filter_insCols = ['campaign_id', 'filter_id', 'fb_object_id', 'rand_cdf']
        dbInsert('campaign_fb_objects', 'campaign_fb_object_id', filter_insCols, filter_rows, 'campaign_id', campaignId, replaceAll=True)
        numRows = len(filter_rows)

    if (genericTupes):
        generic_rows = []
        for fbObjectId, prob in genericTupes:
            generic_rows.append({
                        'campaign_id' : campaignId,
                        'fb_object_id' : fbObjectId,
                        'rand_cdf' : prob
                        })

        generic_insCols = ['campaign_id', 'fb_object_id', 'rand_cdf']
        dbInsert('campaign_generic_fb_objects', 'campaign_generic_fb_object_id', generic_insCols, generic_rows, 'campaign_id', campaignId, replaceAll=True)
        numRows += len(generic_rows)

    return numRows

"""
NOTE:
Will also need functions for models/algorithms, 
but punting on those for now...
"""

def dbGetClient(clientId, cols):
    """Get the specified columns associated with a client_id"""
    sql = "SELECT " + ', '.join(cols) + " FROM clients WHERE client_id=" + str(clientId)
    conn = db.getConn()
    curs = conn.cursor()

    try:
        curs.execute(sql)
        ret = curs.fetchall()
    finally:
        conn.close()

    return ret


def dbGetObject(table, cols, objectIndex, objectId):
    """Get the specified columns associated with a given current object.
    For instance, might call: dbGetObject('filters', ['name', 'description'], 'filter_id', 42)
    """
    sql = "SELECT " + ', '.join(cols) + " FROM " + table + " WHERE " + objectIndex + "=" + str(objectId) + " AND NOT is_deleted"
    conn = db.getConn()
    curs = conn.cursor()

    try:
        curs.execute(sql)
        ret = curs.fetchall()
    finally:
        conn.close()

    return ret


def dbGetObjectAttributes(table, cols, objectIndex, objectId):
    """Get the specified columns associated with a given object's attributes.
    This is mainly distinguished from above by referencing "end_dt" to determine that a 
    row is current, rather than an object's "is_deleted" field. Could probably combine
    this with above with an extra param for that...

    Example call: dbGetObjectAttributes('filter_features', ['feature', 'operator', 'value', 'value_type'], 'filter_id', 23)
    """
    sql = "SELECT " + ', '.join(cols) + " FROM " + table + " WHERE " + objectIndex + "=" + str(objectId) + " AND end_dt IS NULL"
    conn = db.getConn()
    curs = conn.cursor()

    try:
        curs.execute(sql)
        ret = curs.fetchall()
    finally:
        conn.close()

    return ret


def dbGetExperimentTupes(table, index, objectKey, keyTupes, extraCols=None):
    """Get the rows that define an A/B test over a certain object type.

    index is the column name for the table's index, used to track the 
      records that define the experiment in logging.
    objectKey is the column name for the object type that is being
      chosen experimentally.
    keyTupes defines the scope of the experiment and can be 
      [(campaign_id, id)] or [(campaign_id, id), (filter_id, id)]
      (the latter is in case of FB Object)
    extraCols is optional and provided to allow for grabbing additional 
      info that is specified at the level of the experiment (such as the 
      'allow_generic' field for choice sets)

    Example call: dbGetExperimentTupes('camapign_global_filters', 'campaign_global_filter_id', 'filter_id', [('campaign_id', 16)])
    """
    where = ' AND '.join(['='.join(map(str, t)) for t in keyTupes])
    ecsql = ''
    if (extraCols):
        ecsql = ', '+', '.join(extraCols)
    sql = "SELECT " + index + ", " + objectKey + ", rand_cdf" + ecsql + " FROM " + table + " WHERE " + where + " AND end_dt IS NULL"
    conn = db.getConn()
    curs = conn.cursor()

    try:
        curs.execute(sql)
        ret = curs.fetchall()   # returns (index, object_id, cdf_prob)
    finally:
        conn.close()

    tupes = sorted([(r[1], r[2]) for r in ret], key=lambda t: t[1])
    checkCDF(tupes)

    return ret


def dbWriteAssignment(sessionId, campaignId, contentId, featureType, featureRow, randomAssign, chosenFromTable, chosenFromRows, background=False):
    """Record an assignment to a given condition to the database.
    Used for logging and later experimental purposes.

    This function simply passes parameters through to _dbWriteAssignment()
    either in the current thread or a background one, depending on the
    background parameter's value"""
    if (background):
        t = threading.Thread(target=_dbWriteAssignment, args=(sessionId, campaignId, contentId, featureType, featureRow, randomAssign, chosenFromTable, chosenFromRows))
        t.daemon = False
        t.start()
        logger.debug("dbWriteAssignment() spawning background thread %d for %s:%s from session %s", t.ident, featureType, featureRow, sessionId)
        return 0
    else:
        logger.debug("dbWriteAssignment() foreground thread %d for %s:%s from session %s", threading.current_thread().ident, featureType, featureRow, sessionId)
        return _dbWriteAssignment(sessionId, campaignId, contentId, featureType, featureRow, randomAssign, chosenFromTable, chosenFromRows)


# helper function that may get run in a background thread
def _dbWriteAssignment(sessionId, campaignId, contentId, featureType, featureRow, randomAssign, chosenFromTable, chosenFromRows):
    """Function that actually records an assignment to the database."""
    tim = datastructs.Timer()
    conn = db.getConn()
    curs = conn.cursor()

    row = {
            'session_id' : sessionId, 
            'campaign_id' : campaignId,
            'content_id' : contentId,
            'feature_type' : featureType,
            'feature_row' : featureRow,
            'random_assign' : randomAssign,
            'chosen_from_table' : chosenFromTable,
            'chosen_from_rows' : str(sorted([int(r) for r in chosenFromRows]))
          }
    sql = """INSERT INTO assignments (session_id, campaign_id, content_id, feature_type, feature_row, random_assign, chosen_from_table, chosen_from_rows) 
                VALUES (%(session_id)s, %(campaign_id)s, %(content_id)s, %(feature_type)s, %(feature_row)s, %(random_assign)s, %(chosen_from_table)s, %(chosen_from_rows)s) """

    try:
        curs.execute(sql, row)
        conn.commit()
    finally:
        conn.close()

    logger.debug("_dbWriteAssignment() thread %d wrote %s:%s assignment from session %s", threading.current_thread().ident, featureType, featureRow, sessionId)
    
    return 1


def updateMetadata(table, index, objectCol, objectId, metadata, replaceAll=False):
    """Update the metadata table for a given object."""

    if (not metadata):
        return 0    # no records to insert

    rows = []
    newNames = []
    for name, value in metadata:

        # Check if we're trying to insert the same key more than once
        if (name in newNames):
            raise ValueError("Names must be unique for metadata. Duplicate found for %s in %s" % (name, table))

        newNames.append(name)
        rows.append({
                    objectCol : objectId, 
                    'name' : name, 
                    'value' : value
                    })

    insCols = [objectCol, 'name', 'value']
    uniqueCols = ['name']

    dbInsert(table, index, insCols, rows, objectCol, objectId, uniqueCols, replaceAll=replaceAll)

    return len(rows)


def doRandAssign(tupes):
    """takes a set of tuples of (id, cdf probability) and chooses one id randomly"""

    tupes = sorted(tupes, key=lambda t: t[1])   # ensure sorted by CDF Probability
    checkCDF(tupes)

    rand = random.random()

    # Pick out smallest probability greater than (or equal to) random number
    for objId, prob in tupes:
        if prob >= rand:
            return objId

    raise CDFProbsError("Math must be broken if we got here...")


def checkCDF(tupes):
    """Takes tuples of (id, CDF Probability) and ensures the CDF is well-defined"""

    probs = sorted([t[1] for t in tupes])
    if (min(probs) <= 0):
        raise CDFProbsError("Zero or negative probabilities detected")
    if (max(probs) != 1.0):
        raise CDFProbsError("Max probability is not 1.0")
    if (len(probs) != len(set(probs))):
        raise CDFProbsError("Duplicate values found in CDF")


def dbSetEndDate(table, index, endIds, connP=None):
    """Set the end_dt for a set of records, removing them from use."""

    conn = connP if (connP is not None) else db.getConn()
    curs = conn.cursor()

    sql = "UPDATE" + table + "SET end_dt = CURRENT_TIMESTAMP WHERE " + index + " IN (" + ','.join([str(i) for i in endIds]) + ")"

    try:
        curs.execute(sql)
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        if (connP is None):
            conn.close()

    return len(endIds)


def dbInsert(table, index, insCols, rows, objectCol=None, objectId=None, uniqueCols=None, connP=None, replaceAll=False):
    """Insert rows into the specified table.
       If replaceAll is true, any current records associated with the given object
       will be removed (by setting their end_dt). Otherwise, if uniqueCols are specified,
       only existing records that conflict with new ones will be removed."""

    rows = rows if (rows is not None) else []

    conn = connP if (connP is not None) else db.getConn()
    curs = conn.cursor()

    insSQL = "INSERT INTO " + table + " (" + ', '.join(insCols) + ") VALUES (" + ', '.join(['%('+c+')s' for c in insCols]) + ")"

    try:
        replaceIds = []
        if (uniqueCols and not replaceAll):
            curs.execute("SELECT " + index + ", " + ', '.join(uniqueCols) + " FROM " + table + " WHERE " + objectCol + " = " + objectId + " AND end_dt IS NULL FOR UPDATE")
            currRecs = { tuple(r[1:]) : int(r[0]) for r in curs }

            for row in rows:
                repId = currRecs.get(tuple(row[u] for u in uniqueCols))
                replaceIds += [repId] if repId is not None else []

        if (replaceAll):
            prepsql = "UPDATE " + table + " SET end_dt = CURRENT_TIMESTAMP WHERE " + objectCol + " IN (" + str(objectId) + ")"
        elif (replaceIds):
            prepsql = "UPDATE " + table + " SET end_dt = CURRENT_TIMESTAMP WHERE " + index + " IN (" + ','.join([str(i) for i in replaceIds]) + ")"
        else:
            prepsql = None

        if (prepsql): 
            logging.debug(prepsql)
            curs.execute(prepsql)
        for row in rows:
            logging.debug(insSQL)
            logging.debug(row)
            curs.execute(insSQL, row)
        newId = curs.lastrowid

        conn.commit()

    except:
        conn.rollback()
        raise

    finally:
        if (connP is None):
            conn.close()

    return newId


class Filter(object):
    def __init__(self, filterId, features):
        """A class to hold filters and associated functionality

        filterId should be the ID from our database
        features should be a list of tupes: [(feature, operator, value)]
        """
        self.filterId = int(filterId)
        self.features = features
        self.str_func = {
                            "min": lambda x, y: x >= y, 
                            "max": lambda x, y: x <= y, 
                            "eq": lambda x, y: x == y,
                            "in": lambda x, l: x in l 
                        }

    def filterFriend(self, user):
        """Determine if the given user object passes the current filter object.

        Note that we implicitly assume an "AND" relationship between all the
        feature/operator sets that define the filter. Will likely want more
        complex logic in the future.
        """
        for feature, operator, value in self.features:
            if not (hasattr(user, feature) and self.str_func[operator](user.__dict__[feature], value)):
                return False

        return True    # user made it through all the filters

    def filterEdgesBySec(self, edges):
        """Given a list of edge objects, return those objects for which
        the secondary passes the current filter."""
        edgesgood = [e for e in edges if self.filterFriend(e.secondary)]
        return edgesgood

class ChoiceSetFilter(Filter):
    def __init__(self, choiceSetFilterId, filterId, urlSlug, modelType=None, features=None, filterObj=None):
        """A class to hold filters associated with a choice set
        (in particular, this means holding onto a choice_set_filter_id,
        a url slug, and a propensity model type).

        May be initialized with either an existing Filter object or
        a list of feature tuples of form [(feature, operator, value)]"""

        if (features is not None and filterObj is not None):
            raise ValueError("Only specify one of features or filterObj")
        elif (features is not None):
            super(ChoiceSetFilter, self).__init__(filterId, features)
        elif (filterObj is not None):
            super(ChoiceSetFilter, self).__init__(filterId, filterObj.features)
        else:
            raise ValueError("Must specify either features or filterObj")

        self.choiceSetFilterId = int(choiceSetFilterId)
        self.urlSlug = urlSlug
        self.modelType = modelType

class ChoiceSet(object):
    def __init__(self, choiceSetId, choiceSetFilters):
        """A class to represent choice sets and associated choice logic.

        choiceSetId refers to the id for this choice set in our DB.
        choiceSetFilters should be a list of ChoiceSetFilter objects
        """
        self.choiceSetId = int(choiceSetId)
        self.choiceSetFilters = choiceSetFilters
        self.sortFunc = lambda el: (len(el), sum([e.score for e in el])/len(el) if el else 0)

    def chooseBestFilter(self, edges, useGeneric=False, minFriends=2, eligibleProportion=0.5):
        """Determine the best choice set filter from a list of edges based on
        the filter that passes the largest number of secondaries (average score
        is used for tie breaking)

        useGeneric specifies whether the choice set should fall back to friends
          who fall in ANY bin if there not enough friends in a single bin.
        minFriends is the minimum number of friends that must be returned,
          otherwise, we'll raise a TooFewFriendsError.
        eligibleProportion specifies the top fraction (based on score) of friends
          that should even be considered here (if we want to restrict only to
          those friends with a reasonable proximity to the primary).
        """
        edgesSort = sorted(edges, key=lambda x: x.score, reverse=True)
        elgCount = int(len(edges) * eligibleProportion)
        edgesElg = edgesSort[:elgCount]  # only grab the top x% of the pool
        
        filteredEdges = [(f, f.filterEdgesBySec(edgesElg)) for f in self.choiceSetFilters]
        sortedFilters = sorted(filteredEdges, key=lambda t: self.sortFunc(t[1]), reverse=True)

        if (len(sortedFilters[0][1]) < minFriends):

            if (not useGeneric):
                raise TooFewFriendsError("Too few friends were available after filtering")

            genericFriends = set(e.secondary.id for t in sortedFilters for e in t[1])
            if (len(genericFriends) < minFriends):
                raise TooFewFriendsError("Too few friends were available after filtering")
            else:
                return (None, [e for e in edgesElg if e.secondary.id in genericFriends])

        return sortedFilters[0]


class TooFewFriendsError(Exception):
    """Too few friends found in picking best choice set filter"""
    pass

class CDFProbsError(Exception):
    """CDF defined by provided experimental probabilities is not well-defined"""
    pass
