import logging

from targetshare import database as db, utils


logger = logging.getLogger(__name__)


def checkDbCDFs(cdfTable, keyCols, objectCol, curs):
    """Reads the current CDFs from a given experiment table and validates they are well-formed"""
    numKeys = len(keyCols)
    sql = ("SELECT " +
          ', '.join(keyCols + [objectCol]) +
          ", rand_cdf FROM " +
          cdfTable +
          " WHERE end_dt IS NULL")
    curs.execute(sql) # SQLi
    rows = curs.fetchall()
    rows = [(tuple(r[:numKeys]), r[numKeys], r[numKeys + 1]) for r in rows]

    cdfs = {}
    for key, objectId, cdfProb in rows:
        cdfs[key] = cdfs.get(key, []) + [(objectId, cdfProb)]

    badCDFs = []
    for key, tupes in cdfs.items():
        try:
            utils.check_cdf(tupes)
        except utils.CDFProbsError as e:
            logger.error("Bad CDF found in %s for %s=%s: %s", (cdfTable, str(keyCols), str(key), str(e)))
            badCDFs.append(key)

    if (not badCDFs):
        logger.debug("All CDFs are well-defined in %s" % cdfTable)

    return badCDFs


def runDbCheck(curs, sql, errorMsg, okMsg, errorRecsFn=None):
    """Run a single DB check, which should return identifiers for any
       records that fail the check. errorRecsFn should return a string
       to be inserted into errorMsg via python string substitution.

    """
    if (errorRecsFn is None):
        errorRecsFn = lambda r: str(r[0])

    curs.execute(sql) # SQLi
    rows = curs.fetchall()

    if (rows):
        badRecs = ', '.join([errorRecsFn(r) for r in rows])
        logger.error(errorMsg % badRecs)
    else:
        logger.debug(okMsg)

    return rows


def validateClientDb():
    """Run several validation checks against the DB client schema"""
    logger.debug("=========== Running Client DB Validation ===========")

    conn = db.getConn()
    curs = conn.cursor()

    # Every client has an app_name and app_id
    sql = """SELECT DISTINCT client_id FROM clients
            WHERE ( fb_app_id IS NULL OR fb_app_id = ''
                    OR fb_app_name IS NULL OR fb_app_name = '');"""

    runDbCheck(curs, sql,
        "FB Params missing for clients: %s",
        "FB Params have been set for all clients")

    # Clients are unique on subdomain.domain
    sql = """SELECT subdomain, domain, COUNT(*) FROM clients
             GROUP BY 1,2 HAVING COUNT(*) > 1;"""

    runDbCheck(curs, sql,
        "Duplicate records for domains: %s",
        "All domains are unique to client",
        errorRecsFn=lambda r: r[0] + '.' + r[1])

    # Every campaign specifies a faces url
    sql = """SELECT DISTINCT cmp.campaign_id FROM campaigns cmp
                    LEFT JOIN campaign_properties props
                    ON cmp.campaign_id = props.campaign_id AND props.end_dt IS NULL
                    WHERE NOT cmp.is_deleted
                    AND (props.client_faces_url IS NULL OR props.client_faces_url = '');"""

    runDbCheck(curs, sql,
        "Faces URL missing for campaigns: %s",
        "All campaigns have a faces URL specified")

    # Every campaign specifies a thank you url
    sql = """SELECT DISTINCT cmp.campaign_id FROM campaigns cmp
                    LEFT JOIN campaign_properties props
                    ON cmp.campaign_id = props.campaign_id AND props.end_dt IS NULL
                    WHERE NOT cmp.is_deleted
                    AND (props.client_thanks_url IS NULL OR props.client_thanks_url = '');"""

    runDbCheck(curs, sql,
        "Thank you URL missing for campaigns: %s",
        "All campaigns have a thank you URL specified")

    # Every campaign specifies an error url
    sql = """SELECT DISTINCT cmp.campaign_id FROM campaigns cmp
                    LEFT JOIN campaign_properties props
                    ON cmp.campaign_id = props.campaign_id AND props.end_dt IS NULL
                    WHERE NOT cmp.is_deleted
                    AND (props.client_error_url IS NULL OR props.client_error_url = '');"""

    runDbCheck(curs, sql,
        "Error URL missing for campaigns: %s",
        "All campaigns have a error URL specified")

    # No campaign specifies itself as a fallback
    # (because infinite loops tend to increase our average time to return content to a user...)
    # I guess you could still accomplish an infinite loop by having two campaigns that
    # fall back to each other. Not sure if it's really worth trying to detect that...
    sql = """SELECT DISTINCT campaign_id FROM campaign_properties
                    WHERE end_dt IS NULL
                    AND fallback_campaign_id = campaign_id;"""

    runDbCheck(curs, sql,
        "Campaigns that fallback to themselves: %s",
        "No campaigns fallback to themselves")

    # Fallback campaign client_id matches parent campaign client_id
    sql = """SELECT DISTINCT cmp1.campaign_id FROM campaign_properties props
                    JOIN campaigns cmp1 on props.campaign_id = cmp1.campaign_id
                    JOIN campaigns cmp2 on props.fallback_campaign_id = cmp2.campaign_id
                    WHERE props.end_dt IS NULL
                    AND NOT cmp1.is_deleted
                    AND cmp1.client_id != cmp2.client_id;"""

    runDbCheck(curs, sql,
        "Campaigns that specify a fallback campaign belonging to another client: %s",
        "No campaigns specify a fallback campaign belonging to another client")

    # Fallback content client_id matches parent campaign client_id
    sql = """SELECT DISTINCT cmp1.campaign_id FROM campaign_properties props
                    JOIN campaigns cmp1 on props.campaign_id = cmp1.campaign_id
                    JOIN client_content cnt2 on props.fallback_content_id = cnt2.content_id
                    WHERE props.end_dt IS NULL
                    AND NOT cmp1.is_deleted
                    AND cmp1.client_id != cnt2.client_id;"""

    runDbCheck(curs, sql,
        "Campaigns that specify fallback content belonging to another client: %s",
        "No campaigns specify fallback content belonging to another client")

    # Every campaign has at least one global filter?
    sql = """SELECT DISTINCT cmp.campaign_id FROM campaigns cmp
                    LEFT JOIN campaign_global_filters filt
                    ON cmp.campaign_id = filt.campaign_id AND filt.end_dt IS NULL
                    WHERE NOT cmp.is_deleted AND filt.filter_id IS NULL;"""

    runDbCheck(curs, sql,
        "Global filters missing for campaigns: %s",
        "All campaigns have at least one global filter")

    # Every campaign has at least one choice set?
    sql = """SELECT DISTINCT cmp.campaign_id FROM campaigns cmp
                    LEFT JOIN campaign_choice_sets cs
                    ON cmp.campaign_id = cs.campaign_id AND cs.end_dt IS NULL
                    WHERE NOT cmp.is_deleted AND cs.choice_set_id IS NULL;"""

    runDbCheck(curs, sql,
        "Choice sets missing for campaigns: %s",
        "All campaigns have at least one choice set")

    # Every choice set has at least one filter?
    sql = """SELECT DISTINCT cs.choice_set_id FROM choice_sets cs
                    LEFT JOIN choice_set_filters csf
                    ON cs.choice_set_id = csf.choice_set_id AND csf.end_dt IS NULL
                    WHERE NOT cs.is_deleted AND csf.filter_id IS NULL;"""

    runDbCheck(curs, sql,
        "Filters missing for choice sets: %s",
        "All choice sets have at least one filter")

    # Any choice set filter specifying a url_slug is url safe
    # (but note that not every object must specify a slug)
    sql = """SELECT DISTINCT choice_set_filter_id FROM choice_set_filters
                    WHERE end_dt IS NOT NULL AND url_slug IS NOT NULL
                    AND url_slug RLIKE '[^A-z0-9%_.~\\|-]';"""

    runDbCheck(curs, sql,
        "Choice set filters with URL-unsafe slugs: %s",
        "All choice set filter URL slugs are URL-safe")

    # Any campaign specifying a generic_url_slug is url safe
    # (but note that not every campaign must specify a slug)
    sql = """SELECT DISTINCT campaign_choice_set_id FROM campaign_choice_sets
                    WHERE end_dt IS NOT NULL AND generic_url_slug IS NOT NULL
                    AND generic_url_slug RLIKE '[^A-z0-9%_.~\\|-]';"""

    runDbCheck(curs, sql,
        "Campaign choice sets with URL-unsafe generic slugs: %s",
        "All campaign choice set generic URL slugs are URL-safe")

    # Full coverage of FB Objects over campaign choice set filters
    sql = """SELECT DISTINCT ccs.campaign_id, csf.filter_id
                    FROM campaign_choice_sets ccs
                    JOIN choice_set_filters csf USING(choice_set_id)
                    LEFT JOIN campaign_fb_objects cfb
                    ON ccs.campaign_id = cfb.campaign_id AND csf.filter_id = cfb.filter_id AND cfb.end_dt IS NULL
                    WHERE ccs.end_dt IS NULL AND csf.end_dt IS NULL AND cfb.fb_object_id IS NULL;"""

    runDbCheck(curs, sql,
        "FB Objects missing for (campaign_id, filter_id) sets: %s",
        "Every campaign choice set filter is associated with a FB object",
        errorRecsFn=lambda r: str((int(r[0]), int(r[1]))))

    # At least one generic FB Object for any campaign with an "allow_generic" choice set
    sql = """SELECT DISTINCT ccs.campaign_id FROM campaign_choice_sets ccs
                    LEFT JOIN campaign_generic_fb_objects cgfb ON ccs.campaign_id = cgfb.campaign_id AND cgfb.end_dt IS NULL
                    WHERE ccs.end_dt IS NULL AND ccs.allow_generic AND cgfb.fb_object_id IS NULL;"""

    runDbCheck(curs, sql,
        "Generic FB Objects missing for campaigns: %s",
        "Every campaign with an allow_generic choice set is associated with at least one generic FB object")

    # Every filter feature has a feature, operator, value, and value_type
    # Also, every filter operator is in ("eq", "min", "max", "in")
    # Also, every filter value_type is in ("int", "string", "list", "float")
    #
    # NOTE: A filter may have no features in order to pass all...
    sql = """SELECT DISTINCT f.filter_id FROM filters f JOIN filter_features ff USING(filter_id)
                    WHERE NOT f.is_deleted AND ff.end_dt IS NULL
                    AND (ff.feature IS NULL OR ff.operator IS NULL OR ff.value IS NULL OR ff.value_type IS NULL
                        OR ff.operator NOT IN ('eq', 'min', 'max', 'in')
                        OR ff.value_type NOT IN ('int', 'float', 'string', 'list'));"""

    runDbCheck(curs, sql,
        "Features are not well specified for filters: %s",
        "All filters have fully specified features")

    # Global filter CDFs are all well-defined
    checkDbCDFs('campaign_global_filters', ['campaign_id'], 'filter_id', curs)

    # Choice set CDFs are all well-defined
    checkDbCDFs('campaign_choice_sets', ['campaign_id'], 'choice_set_id', curs)

    # Facebook object CDFs are all well-defined
    checkDbCDFs('campaign_fb_objects', ['campaign_id', 'filter_id'], 'fb_object_id', curs)
    checkDbCDFs('campaign_generic_fb_objects', ['campaign_id'], 'fb_object_id', curs)

    # Every FB Object has an og_action, og_type, og_title, og_image, og_description, sharing_prompt
    sql = """SELECT DISTINCT fbo.fb_object_id FROM fb_objects fbo
                    LEFT JOIN fb_object_attributes fboa USING(fb_object_id)
                    WHERE NOT fbo.is_deleted AND
                    (fboa.og_action IS NULL OR fboa.og_type IS NULL OR fboa.og_title IS NULL OR fboa.og_image IS NULL
                     OR fboa.og_description IS NULL OR fboa.sharing_prompt IS NULL);"""

    runDbCheck(curs, sql,
        "Information missing for FB objects: %s",
        "All FB objects contain required information")

    # Any FB object specifying a url_slug is url safe
    # (but note that not every object must specify a slug)
    sql = """SELECT DISTINCT fb_object_id FROM fb_object_attributes
                    WHERE end_dt IS NOT NULL AND url_slug IS NOT NULL
                    AND url_slug RLIKE '[^A-z0-9%_.~\\|-]';"""

    runDbCheck(curs, sql,
        "Facebook objects with URL-unsafe slugs: %s",
        "All Facebook object URL slugs are url-safe")

    # Every filter associated with a current campaign is current/actually exists
    sql = """SELECT DISTINCT cf.filter_id FROM campaign_global_filters cf
                    LEFT JOIN filters f USING(filter_id)
                    WHERE cf.end_dt IS NULL
                    AND (f.is_deleted OR f.filter_id IS NULL);"""

    runDbCheck(curs, sql,
        "Missing filters associated with campaigns: %s",
        "All filters associated with campaigns are accounted for.")

    # Every choice set associated with a current campaign is current/exists
    sql = """SELECT DISTINCT ccs.choice_set_id FROM campaign_choice_sets ccs
                    LEFT JOIN choice_sets cs USING(choice_set_id)
                    WHERE ccs.end_dt IS NULL
                    AND (cs.is_deleted OR cs.choice_set_id IS NULL);"""

    runDbCheck(curs, sql,
        "Missing choice sets associated with campaigns: %s",
        "All choice sets associated with campaigns are accounted for.")

    # Every choice set filter associated with a current campaign is current
    sql = """SELECT DISTINCT csf.filter_id FROM campaign_choice_sets ccs
                    JOIN choice_set_filters csf USING(choice_set_id)
                    LEFT JOIN filters f USING(filter_id)
                    WHERE ccs.end_dt IS NULL
                    AND (f.is_deleted OR f.filter_id IS NULL);"""

    runDbCheck(curs, sql,
        "Missing choice set filters associated with campaigns: %s",
        "All choice set filters associated with campaigns are accounted for.")

    # Every FB object associated with a current campaign/filter combo is current
    sql = """SELECT DISTINCT cfb.fb_object_id FROM campaign_fb_objects cfb
                    LEFT JOIN fb_objects fbo USING(fb_object_id)
                    WHERE cfb.end_dt IS NULL
                    AND (fbo.is_deleted OR fbo.fb_object_id IS NULL);"""

    runDbCheck(curs, sql,
        "Missing FB objects associated with campaigns: %s",
        "All FB objects associated with campaigns are accounted for.")

    # Every fallback campaign associated with a current campaign is current/actually exists
    sql = """SELECT DISTINCT props.campaign_id FROM campaign_properties props
                    LEFT JOIN campaigns cmp ON props.fallback_campaign_id = cmp.campaign_id
                    WHERE props.end_dt IS NULL AND props.fallback_campaign_id IS NOT NULL
                    AND (cmp.is_deleted OR cmp.campaign_id IS NULL);"""

    runDbCheck(curs, sql,
        "Missing fallback campaigns associated with campaigns: %s",
        "All fallback campaigns associated with campaigns are accounted for.")

    # Every fallback content associated with a current campaign is current/actually exists
    sql = """SELECT DISTINCT props.campaign_id FROM campaign_properties props
                    LEFT JOIN client_content cnt ON props.fallback_content_id = cnt.content_id
                    WHERE props.end_dt IS NULL AND props.fallback_content_id
                    AND (cnt.is_deleted OR cnt.content_id IS NULL);"""

    runDbCheck(curs, sql,
        "Missing fallback content associated with campaigns: %s",
        "All fallback content associated with campaigns are accounted for.")

    conn.rollback()

    logger.debug("=========== Finished Client DB Validation ===========")
