#!/usr/bin/env python

"""NOTE:
   Really quickly hacked together from my straight .sql file.
   Might want to migrate this to something else, but if we consider
   moving to an ORM, doesn't seem worth that at the moment.
"""

import logging

from . import database_compat as db
from .settings import config 

logger = logging.getLogger(__name__)

def client_db_reset():
    """Drop and re-create all of the client/campaign tables.
    Doesn't touch users, edges, tokens, or events."""

    conn = db.getConn()
    curs = conn.cursor()

    # Table to keep track of all our clients
    sql = """DROP TABLE IF EXISTS clients;"""
    curs.execute(sql)
    sql = """
        CREATE TABLE clients (
            client_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(256),
            fb_app_name VARCHAR(256),
            fb_app_id VARCHAR(256),
            domain VARCHAR(256),
            subdomain VARCHAR(256),
            create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY (name),
            UNIQUE KEY (domain, subdomain)
        );
    """
    curs.execute(sql)

    # Table to define associations between users and clients they've connected to
    #
    # Does this need a way to identify "disconnected"??
    """NOTE: This will eventually move to our dynamo/mango-type of store"""

    sql = "DROP TABLE IF EXISTS user_clients;"
    curs.execute(sql)
    sql = """
        CREATE TABLE user_clients (
            fbid BIGINT,
            client_id INT,
            create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (fbid, client_id),
            KEY(fbid),
            KEY(client_id)
        );
    """
    curs.execute(sql)

    # Table to track assignment of users to various objects (randomly or otherwise),
    # constituting the log of every choice that was made on the back-end during the
    # user flow.
    """NOTE: This will eventually end up in our 'logging' data store"""

    sql = "DROP TABLE IF EXISTS assignments;"
    curs.execute(sql)
    sql = """    
        CREATE TABLE assignments (
            session_id VARCHAR(128),
            campaign_id INT,
            content_id INT,
            feature_type VARCHAR(128),
            feature_row INT,
            random_assign BOOLEAN,
            assign_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            chosen_from_table VARCHAR(128),
            chosen_from_rows VARCHAR(128),
            KEY (session_id)
        );
    """
    curs.execute(sql)


    # These are the URL's that we'll be redirecting to. May be parameterized by the
    # URL slugs associated with the FB object and/or choice set filter chosen for a
    # given user, allowing the client to serve different content for each combination.
    # (naturally, it will be up to the client to ensure that these landing pages exist)
    # Parameterized such as: # http://client.domain.com/some/content/{{fb_obj_slug}}/{{choice_set_slug}}?some=params
    sql = "DROP TABLE IF EXISTS client_content;"
    curs.execute(sql)
    sql = """
        CREATE TABLE client_content (
            content_id INT AUTO_INCREMENT PRIMARY KEY,
            client_id INT,
            name VARCHAR(256),
            description VARCHAR(1024),
            url VARCHAR(2048),
            is_deleted BOOLEAN DEFAULT False,
            create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            delete_dt TIMESTAMP NULL DEFAULT NULL,
            KEY(client_id)
        );
    """
    curs.execute(sql)


    # Default values for various client objects to allow a client to get up and
    # running more quickly, only having to actually change these if they want
    # something different or to run an experiment. We'll likely want to preload
    # some generic styles, models, full-pass filter, etc.
    sql = "DROP TABLE IF EXISTS client_defaults;"
    curs.execute(sql)
    sql = """
    CREATE TABLE client_defaults (
        client_default_id INT AUTO_INCREMENT PRIMARY KEY,
        client_id INT,
        button_style_id INT,
        faces_style_id INT,
        propensity_model_id INT,
        proximity_model_id INT,
        mix_model_id INT,
        filter_id INT,
        choice_set_id INT,
        choice_set_algorithm_id INT,
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(client_id),
        KEY(client_id, end_dt)
    );
    """
    curs.execute(sql)


    # Top-level definitions of the campaigns a client might run.
    sql = "DROP TABLE IF EXISTS campaigns;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaigns (
        campaign_id INT AUTO_INCREMENT PRIMARY KEY,
        client_id INT,
        name VARCHAR(256),
        description VARCHAR(1024),
        is_deleted BOOLEAN DEFAULT False,
        create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delete_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(client_id)
    );
    """
    curs.execute(sql)


    # Campaign-level properties, such as where a button click takes you (client_faces_url, on the client server)
    # and fallback behavior (such as a "special friends" campaign & content)
    sql = "DROP TABLE IF EXISTS campaign_properties;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaign_properties (
        campaign_property_id INT AUTO_INCREMENT PRIMARY KEY,
        campaign_id INT,
        client_faces_url VARCHAR(2096),
        client_thanks_url VARCHAR(2096),
        client_error_url VARCHAR(2096),
        fallback_campaign_id INT,
        fallback_content_id INT,
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(campaign_id),
        KEY(campaign_id, end_dt)
    );
    """
    curs.execute(sql)


    # Meta data for campaigns
    sql = "DROP TABLE IF EXISTS campaign_meta;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaign_meta (
        campaign_meta_id INT AUTO_INCREMENT PRIMARY KEY,
        campaign_id INT,
        name VARCHAR(256),
        value VARCHAR(1024),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(campaign_id)
    );
    """
    curs.execute(sql)


    """------------------- FILTERS -------------------"""

    # Top-level defitions of the filters created by a client
    sql = "DROP TABLE IF EXISTS filters;"
    curs.execute(sql)
    sql = """
    CREATE TABLE filters (
        filter_id INT AUTO_INCREMENT PRIMARY KEY,
        client_id INT,
        name VARCHAR(256),
        description VARCHAR(1024),
        is_deleted BOOLEAN DEFAULT False,
        create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delete_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(client_id)
    );
    """
    curs.execute(sql)


    # Meta data for filters
    sql = "DROP TABLE IF EXISTS filter_meta;"
    curs.execute(sql)
    sql = """
    CREATE TABLE filter_meta (
        filter_meta_id INT AUTO_INCREMENT PRIMARY KEY,
        filter_id INT,
        name VARCHAR(256),
        value VARCHAR(1024),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(filter_id)
    );
    """
    curs.execute(sql)


    # Actual definition of the filter; a given filter may have multiple
    # rows in this table, for instance, "age min 18" + "age max 29" +
    # "state in ['IL', 'CA', 'NV']" + "gender equals male" as four rows
    # to define a filter for males between 18 & 29 in IL, CA, or NV.
    # (Presumption will be to "AND" rows -- may need to implement more
    # complex logic eventually)
    sql = "DROP TABLE IF EXISTS filter_features;"
    curs.execute(sql)
    sql = """
    CREATE TABLE filter_features (
        filter_feature_id INT AUTO_INCREMENT PRIMARY KEY,
        filter_id INT,
        feature VARCHAR(64),
        operator VARCHAR(32),
        value VARCHAR(1024),
        value_type VARCHAR(32),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(filter_id),
        KEY(filter_id, end_dt)
    );
    """
    curs.execute(sql)


    # Define the global filters to apply to each campaign, with ability
    # to experimentally choose one among a set associated with the campaign
    sql = "DROP TABLE IF EXISTS campaign_global_filters;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaign_global_filters (
        campaign_global_filter_id INT AUTO_INCREMENT PRIMARY KEY,
        campaign_id INT,
        filter_id INT,
        rand_cdf NUMERIC(10,9),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(campaign_id),
        KEY(campaign_id, end_dt),
        KEY(filter_id)
    );
    """
    curs.execute(sql)


    """------------------- CHOICE SETS -------------------"""

    # "Choice sets" are basically bags of filters over which a given primary will
    # be shown friends that fit just one of these filters and asked to share
    # content particular to that filter. For instance, OFA might run a "call your
    # senator campaign" and want to show someone friends in one of a handful of
    # targeted states (say, IL, CA, or NV), calling out their senator by name in
    # the facebook message itself. Whether the primary is shown friends in IL, CA,
    # or NV will be based on the state in which they have the most friends or
    # potential for influence...

    # Top-level defitions of the choice sets created by a client
    sql = "DROP TABLE IF EXISTS choice_sets;"
    curs.execute(sql)
    sql = """
    CREATE TABLE choice_sets (
        choice_set_id INT AUTO_INCREMENT PRIMARY KEY,
        client_id INT,
        name VARCHAR(256),
        description VARCHAR(1024),
        is_deleted BOOLEAN DEFAULT False,
        create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delete_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(client_id)
    );
    """
    curs.execute(sql)


    # Meta data for choice sets
    sql = "DROP TABLE IF EXISTS choice_set_meta;"
    curs.execute(sql)
    sql = """
    CREATE TABLE choice_set_meta (
        choice_set_meta_id INT AUTO_INCREMENT PRIMARY KEY,
        choice_set_id INT,
        name VARCHAR(256),
        value VARCHAR(1024),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(choice_set_id)
    );
    """
    curs.execute(sql)


    # Actual definition of each choice set, basically just a bag of filters. Also
    # note that we specify here a url slug that can be passed through to the client's
    # page in order to allow them to serve different content...
    sql = "DROP TABLE IF EXISTS choice_set_filters;"
    curs.execute(sql)
    sql = """
    CREATE TABLE choice_set_filters (
        choice_set_filter_id INT AUTO_INCREMENT PRIMARY KEY,
        choice_set_id INT,
        filter_id INT,
        url_slug VARCHAR(64),
        propensity_model_type VARCHAR(32),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(choice_set_id),
        KEY(choice_set_id, end_dt)
    );
    """
    curs.execute(sql)


    # Define the choice sets that can be used for each campaign, with ability to
    # randomly choose one if several are provided (note that this random choice
    # would be between say [IL, CA, NV] vs [IA, OH, FL] -- choosing a particular
    # state is non-random and based on a specific decision rule)
    #
    # Here, "allow_generic" is provided to let the client specify whether they
    # want to use a generic message for friends across all choice set filters
    # in the event that there are too few friends in any one filter. In that
    # case, the generic_url_slug will be passed through, rather than the slug
    # associated with that choice set filter.
    sql = "DROP TABLE IF EXISTS campaign_choice_sets;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaign_choice_sets (
        campaign_choice_set_id INT AUTO_INCREMENT PRIMARY KEY,
        campaign_id INT,
        choice_set_id INT,
        rand_cdf NUMERIC(10,9),
        allow_generic BOOLEAN,
        generic_url_slug VARCHAR(64),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(campaign_id),
        KEY(campaign_id, end_dt),
        KEY(choice_set_id)
    );
    """
    curs.execute(sql)


    """------------------- FACEBOOK OBJECTS -------------------"""

    # Facebook objects actually define what will be shared on Facebook, as well
    # as the suggested messages that we'll provide for the tagging itself.

    # Top-level defitions of the FB objects created by a client
    sql = "DROP TABLE IF EXISTS fb_objects;"
    curs.execute(sql)
    sql = """
    CREATE TABLE fb_objects (
        fb_object_id INT AUTO_INCREMENT PRIMARY KEY,
        client_id INT,
        name VARCHAR(256),
        description VARCHAR(1024),
        is_deleted BOOLEAN DEFAULT False,
        create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delete_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(client_id)    
    );
    """
    curs.execute(sql)


    # Meta data for FB objects
    sql = "DROP TABLE IF EXISTS fb_object_meta;"
    curs.execute(sql)
    sql = """
    CREATE TABLE fb_object_meta (
        fb_object_meta_id INT AUTO_INCREMENT PRIMARY KEY,
        fb_object_id INT,
        name VARCHAR(256),
        value VARCHAR(1024),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(fb_object_id)
    );
    """
    curs.execute(sql)


    # Actual definition of the object -- parameters of what will show up on FB
    #
    # Right now, facebook objects are sort of fixed, not parameterized relative
    # to the choice set filter or to the specific content (eg, if a button is 
    # being placed on several different movies, the object wouldn't be able to
    # refer to the specific movie being shared, just something like "watch the
    # new movie on barackobama.com" -- probably won't be ideal going forward)
    sql = "DROP TABLE IF EXISTS fb_object_attributes;"
    curs.execute(sql)
    sql = """
    CREATE TABLE fb_object_attributes (
        fb_object_attributes_id INT AUTO_INCREMENT PRIMARY KEY,
        fb_object_id INT,
        og_action VARCHAR(64),
        og_type VARCHAR(64),
        og_title VARCHAR(128),
        og_image VARCHAR(2096),
        og_description VARCHAR(1024),
        page_title VARCHAR(256),
        sharing_prompt VARCHAR(2096),
        msg1_pre VARCHAR(1024),
        msg1_post VARCHAR(1024),
        msg2_pre VARCHAR(1024),
        msg2_post VARCHAR(1024),
        url_slug VARCHAR(64),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(fb_object_id),
        KEY(fb_object_id, end_dt)
    );
    """
    curs.execute(sql)


    # Assign the FB objects to a filter (meaning here a potential choice set bin) within a given
    # campaign (allowing for randomization across several FB objects).
    #
    # What I don't like much here is that once we've chosen a choice set filter, we're relying on
    # the existence in this table of a FB object for that filter in this campaign, meaning that we 
    # shouldn't let a client submit changes to the choice sets or campaign-choice_set associations 
    # without also ensuring that all filters that could be applied in any campaign are associated 
    # with FB objects.
    # That seems pretty clunky.
    #
    # For instance, this table would contain the FB objects that could be shared by a user who comes
    # in to the OFA climate legislation campaign (campaign_id) and is being shown friends in IL (filter_id)
    sql = "DROP TABLE IF EXISTS campaign_fb_objects;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaign_fb_objects (
        campaign_fb_object_id INT AUTO_INCREMENT PRIMARY KEY,
        campaign_id INT,
        filter_id INT,
        fb_object_id INT,
        rand_cdf NUMERIC(10,9),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(campaign_id, filter_id),
        KEY(campaign_id, filter_id, end_dt),
        KEY(fb_object_id)
    );
    """
    curs.execute(sql)


    # Facebook objects for "generic" fallbacks from campaign choice sets
    #
    # Could be combined with campaign_fb_objects, but doing so would require either treating entries
    # with NULL filter_id as generic or creating a "dummy" filter that represents generic, neither
    # of which seems too satisfying.
    sql = "DROP TABLE IF EXISTS campaign_generic_fb_objects;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaign_generic_fb_objects (
        campaign_generic_fb_object_id INT AUTO_INCREMENT PRIMARY KEY,
        campaign_id INT,
        fb_object_id INT,
        rand_cdf NUMERIC(10,9),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(campaign_id),
        KEY(campaign_id, end_dt),
        KEY(fb_object_id)
    );
    """
    curs.execute(sql)





    """
        -----------------------------------------------------
        -----------------------------------------------------
        NOTE: Tables from this point down are provided for
              future use. They are not currently accessed by
              the existing user flow (as all of the styles &
              models are presently fixed), but will be as the
              app develops in the future.
        -----------------------------------------------------
        -----------------------------------------------------
    """



    """------------------- BUTTON STYLES -------------------"""

    # Top-level defitions of the button styles created by a client
    sql = "DROP TABLE IF EXISTS button_styles;"
    curs.execute(sql)
    sql = """
    CREATE TABLE button_styles (
        button_style_id INT AUTO_INCREMENT PRIMARY KEY,
        client_id INT,
        name VARCHAR(256),
        description VARCHAR(1024),
        is_deleted BOOLEAN DEFAULT False,
        create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delete_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(client_id)
    );
    """
    curs.execute(sql)


    # Meta data for button styles
    sql = "DROP TABLE IF EXISTS button_style_meta;"
    curs.execute(sql)
    sql = """
    CREATE TABLE button_style_meta (
        button_style_meta_id INT AUTO_INCREMENT PRIMARY KEY,
        button_style_id INT,
        name VARCHAR(256),
        value VARCHAR(1024),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(button_style_id)
    );
    """
    curs.execute(sql)


    # Actual definition of the button style: HTML template and CSS files
    # (should just be file names, code will fill in server, directory, etc.)
    #
    # Or would it be better to just dump the HTML and CSS in the DB and serve
    # it dynamically??
    sql = "DROP TABLE IF EXISTS button_style_files;"
    curs.execute(sql)
    sql = """
    CREATE TABLE button_style_files (
        button_style_file_id INT AUTO_INCREMENT PRIMARY KEY,
        button_style_id INT,
        html_template VARCHAR(128),
        css_file VARCHAR(128),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(button_style_id),
        KEY(button_style_id, end_dt)
    );
    """
    curs.execute(sql)


    # Define the button styles associated with each campaign, with ability
    # to experimentally choose one among a set associated with the campaign
    sql = "DROP TABLE IF EXISTS campaign_button_styles;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaign_button_styles (
        campaign_button_style_id INT AUTO_INCREMENT PRIMARY KEY,
        campaign_id INT,
        button_style_id INT,
        rand_cdf NUMERIC(10,9),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(campaign_id),
        KEY(campaign_id, end_dt),
        KEY(button_style_id)
    );
    """
    curs.execute(sql)


    """------------------- FACES STYLES -------------------"""

    # Top-level defitions of the faces styles created by a client
    sql = "DROP TABLE IF EXISTS faces_styles;"
    curs.execute(sql)
    sql = """
    CREATE TABLE faces_styles (
        faces_style_id INT AUTO_INCREMENT PRIMARY KEY,
        client_id INT,
        name VARCHAR(256),
        description VARCHAR(1024),
        is_deleted BOOLEAN DEFAULT False,
        create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delete_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(client_id)
    );
    """
    curs.execute(sql)


    # Meta data for faces styles
    sql = "DROP TABLE IF EXISTS faces_style_meta;"
    curs.execute(sql)
    sql = """
    CREATE TABLE faces_style_meta (
        faces_style_meta_id INT AUTO_INCREMENT PRIMARY KEY,
        faces_style_id INT,
        name VARCHAR(256),
        value VARCHAR(1024),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(faces_style_id)
    );
    """
    curs.execute(sql)


    # Actual definition of the faces style: HTML template and CSS files
    # (should just be file names, code will fill in server, directory, etc.)
    #
    # Or would it be better to just dump the HTML and CSS in the DB and serve
    # it dynamically??
    sql = "DROP TABLE IF EXISTS faces_style_files;"
    curs.execute(sql)
    sql = """
    CREATE TABLE faces_style_files (
        faces_style_file_id INT AUTO_INCREMENT PRIMARY KEY,
        faces_style_id INT,
        html_template VARCHAR(128),
        css_file VARCHAR(128),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(faces_style_id),
        KEY(faces_style_id, end_dt)
    );
    """
    curs.execute(sql)


    # Define the faces styles associated with each campaign, with ability
    # to experimentally choose one among a set associated with the campaign
    sql = "DROP TABLE IF EXISTS campaign_faces_styles;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaign_faces_styles (
        campaign_faces_style_id INT AUTO_INCREMENT PRIMARY KEY,
        campaign_id INT,
        faces_style_id INT,
        rand_cdf NUMERIC(10,9),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(campaign_id),
        KEY(campaign_id, end_dt),
        KEY(faces_style_id)
    );
    """
    curs.execute(sql)


    """------------------- PROXIMITY MODELS -------------------"""

    # Top-level defitions of the proximity models (note these are not at
    # the client_id level as they're created by us and global to the system)
    sql = "DROP TABLE IF EXISTS proximity_models;"
    curs.execute(sql)
    sql = """
    CREATE TABLE proximity_models (
        proximity_model_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(256),
        description VARCHAR(1024),
        is_deleted BOOLEAN DEFAULT False,
        create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delete_dt TIMESTAMP NULL DEFAULT NULL
    );
    """
    curs.execute(sql)


    # Meta data for proximity models
    sql = "DROP TABLE IF EXISTS proximity_model_meta;"
    curs.execute(sql)
    sql = """
    CREATE TABLE proximity_model_meta (
        proximity_model_meta_id INT AUTO_INCREMENT PRIMARY KEY,
        proximity_model_id INT,
        name VARCHAR(256),
        value VARCHAR(1024),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(proximity_model_id)
    );
    """
    curs.execute(sql)


    # Actual definition of the model. Not really sure on the data structure here.
    sql = "DROP TABLE IF EXISTS proximity_model_definitions;"
    curs.execute(sql)
    sql = """
    CREATE TABLE proximity_model_definitions (
        proximity_model_definition_id INT AUTO_INCREMENT PRIMARY KEY,
        proximity_model_id INT,
        model_definition VARCHAR(4096),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(proximity_model_id),
        KEY(proximity_model_id, end_dt)
    );
    """
    curs.execute(sql)


    # Define the models associated with each campaign, with ability to experimentally 
    # choose one among a set associated with the campaign
    sql = "DROP TABLE IF EXISTS campaign_proximity_models;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaign_proximity_models (
        campaign_proximity_model_id INT AUTO_INCREMENT PRIMARY KEY,
        campaign_id INT,
        proximity_model_id INT,
        rand_cdf NUMERIC(10,9),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(campaign_id),
        KEY(campaign_id, end_dt),
        KEY(proximity_model_id)
    );
    """
    curs.execute(sql)


    """------------------- PROPENSITY MODELS -------------------"""

    # Are the clients choosing these models and associating them with their
    # campaigns or are we? Who sets up the experiments here?

    # Top-level defitions of the propensity models (note these are not at
    # the client_id level as they're created by us and global to the system)
    #
    # (however, we may develop some propensity models specific to particular
    # clients in the future; should think about how that would be implemented)
    sql = "DROP TABLE IF EXISTS propensity_models;"
    curs.execute(sql)
    sql = """
    CREATE TABLE propensity_models (
        proximity_model_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(256),
        description VARCHAR(1024),
        is_deleted BOOLEAN DEFAULT False,
        create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delete_dt TIMESTAMP NULL DEFAULT NULL
    );
    """
    curs.execute(sql)


    # Meta data for propensity models
    sql = "DROP TABLE IF EXISTS propensity_model_meta;"
    curs.execute(sql)
    sql = """
    CREATE TABLE propensity_model_meta (
        propensity_model_meta_id INT AUTO_INCREMENT PRIMARY KEY,
        propensity_model_id INT,
        name VARCHAR(256),
        value VARCHAR(1024),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(propensity_model_id)
    );
    """
    curs.execute(sql)


    # Actual definition of the model. Not really sure on the data structure here.
    # propensity_model_type might be fundraising vs volunteer vs signup, etc. 
    sql = "DROP TABLE IF EXISTS propensity_model_definitions;"
    curs.execute(sql)
    sql = """
    CREATE TABLE propensity_model_definitions (
        propensity_model_definition_id INT AUTO_INCREMENT PRIMARY KEY,
        propensity_model_id INT,
        propensity_model_type VARCHAR(64),
        model_definition VARCHAR(4096),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(propensity_model_id),
        KEY(propensity_model_id, end_dt)
    );
    """
    curs.execute(sql)


    # Define the models associated with each campaign, with ability to experimentally 
    # choose one among a set associated with the campaign
    #
    # Couple of things here -- randomization should occur over each type of model,
    # possibly choosing, say, a volunteer model and a fundraising model for a given
    # campaign if it's possible that either could be used. Do we need to explicitly
    # state somewhere if a certain type is used for the campaign overall??
    #
    # "special-friends" type of fallbacks seem to make this very messy, where we need
    # to define propensity for that, but want a single type of propensity for the 
    # campaign generally.
    sql = "DROP TABLE IF EXISTS campaign_propensity_models;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaign_propensity_models (
        campaign_propensity_model_id INT AUTO_INCREMENT PRIMARY KEY,
        campaign_id INT,
        propensity_model_id INT,
        rand_cdf NUMERIC(10,9),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(campaign_id),
        KEY(campaign_id, end_dt),
        KEY(propensity_model_id)
    );
    """
    curs.execute(sql)


    """------------------- MIX MODELS -------------------"""

    # That is, the model for combining a proximity and propensity score
    #
    # Are the clients choosing these models and associating them with their
    # campaigns or are we? Who sets up the experiments here?

    # Top-level defitions of the mix models (note these are not at
    # the client_id level as they're created by us and global to the system)
    sql = "DROP TABLE IF EXISTS mix_models;"
    curs.execute(sql)
    sql = """
    CREATE TABLE mix_models (
        mix_model_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(256),
        description VARCHAR(1024),
        is_deleted BOOLEAN DEFAULT False,
        create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delete_dt TIMESTAMP NULL DEFAULT NULL
    );
    """
    curs.execute(sql)


    # Meta data for mix models
    sql = "DROP TABLE IF EXISTS mix_model_meta;"
    curs.execute(sql)
    sql = """
    CREATE TABLE mix_model_meta (
        mix_model_meta_id INT AUTO_INCREMENT PRIMARY KEY,
        mix_model_id INT,
        name VARCHAR(256),
        value VARCHAR(1024),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(mix_model_id)
    );
    """
    curs.execute(sql)


    # Actual definition of the model. Not really sure on the data structure here.
    sql = "DROP TABLE IF EXISTS mix_model_definitions;"
    curs.execute(sql)
    sql = """
    CREATE TABLE mix_model_definitions (
        mix_model_definition_id INT AUTO_INCREMENT PRIMARY KEY,
        mix_model_id INT,
        model_definition VARCHAR(4096),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(mix_model_id),
        KEY(mix_model_id, end_dt)
    );
    """
    curs.execute(sql)


    # Define the models associated with each campaign, with ability to experimentally 
    # choose one among a set associated with the campaign
    sql = "DROP TABLE IF EXISTS campaign_mix_models;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaign_mix_models (
        campaign_mix_model_id INT AUTO_INCREMENT PRIMARY KEY,
        campaign_id INT,
        mix_model_id INT,
        rand_cdf NUMERIC(10,9),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(campaign_id),
        KEY(campaign_id, end_dt),
        KEY(mix_model_id)
    );
    """
    curs.execute(sql)


    """------------------- CHOICE SET ALGORITHMS -------------------"""

    # Algorithms for choosing a filter from a choice set, for instance
    # maximizing proximity vs. maximizing number of friends vs. some
    # threshold, etc.
    #
    # Are the clients choosing these models and associating them with their
    # campaigns or are we? Who sets up the experiments here?

    # Top-level defitions of the choice set algorithms (note these are not at
    # the client_id level as they're created by us and global to the system)
    sql = "DROP TABLE IF EXISTS choice_set_algoritms;"
    curs.execute(sql)
    sql = """
    CREATE TABLE choice_set_algoritms (
        choice_set_algorithm_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(256),
        description VARCHAR(1024),
        is_deleted BOOLEAN DEFAULT False,
        create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delete_dt TIMESTAMP NULL DEFAULT NULL
    );
    """
    curs.execute(sql)


    # Meta data for choice set algorithms
    sql = "DROP TABLE IF EXISTS choice_set_algoritm_meta;"
    curs.execute(sql)
    sql = """
    CREATE TABLE choice_set_algoritm_meta (
        choice_set_algoritm_meta_id INT AUTO_INCREMENT PRIMARY KEY,
        choice_set_algoritm_id INT,
        name VARCHAR(256),
        value VARCHAR(1024),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(choice_set_algoritm_id)
    );
    """
    curs.execute(sql)


    # Actual definition of the algorithm. Not really sure on the data structure here.
    sql = "DROP TABLE IF EXISTS choice_set_algoritm_definitions;"
    curs.execute(sql)
    sql = """
    CREATE TABLE choice_set_algoritm_definitions (
        choice_set_algoritm_definition_id INT AUTO_INCREMENT PRIMARY KEY,
        choice_set_algoritm_id INT,
        algorithm_definition VARCHAR(4096),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(choice_set_algoritm_id),
        KEY(choice_set_algoritm_id, end_dt)
    );
    """
    curs.execute(sql)


    # Define the algorithms associated with each campaign, with ability to experimentally 
    # choose one among a set associated with the campaign
    sql = "DROP TABLE IF EXISTS campaign_choice_set_algoritm;"
    curs.execute(sql)
    sql = """
    CREATE TABLE campaign_choice_set_algoritm (
        campaign_choice_set_algoritm_id INT AUTO_INCREMENT PRIMARY KEY,
        campaign_id INT,
        choice_set_algoritm_id INT,
        rand_cdf NUMERIC(10,9),
        start_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_dt TIMESTAMP NULL DEFAULT NULL,
        KEY(campaign_id),
        KEY(campaign_id, end_dt),
        KEY(choice_set_algoritm_id)
    );
    """
    curs.execute(sql)
