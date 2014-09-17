/* module for client campaign list view */
define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/campaignWizard/skeleton',
      'views/miniHeader',
      'models/campaign', 
      'templates/clientCampaigns', 
      'css!styles/clientCampaigns' 
    ],
    function( $, _, Backbone, CampaignWizard, miniHeader, campaign, template ) {

        /* holds a collection of campaign models,
           this model should be used by the wizard */
        var campaignCollection = Backbone.Collection.extend( { model: campaign } );

        return Backbone.View.extend( {
           
            /* model for view's state */ 
            model: new Backbone.Model( { } ),

            /* see sidebar.js for not bloated DOM suggestion */
            events: {
                'click button[data-js="createCampaignBtn"]': 'showNewCampaign',
                'click button[data-js="editButton"]': 'showEditableCampaign',
                'click div[data-js="campaignName"]': 'navToCampaignSummary'
            },

            /* this view is instantiated with a list of campaigns
               (options.campaigns).  A better 
               approach would be to make this an ajax call done by
               a CampaignCollection module that defines a url attribute */
            initialize: function( options ) {

                _.extend( this, options );

                this.model.set('state', 'mainView');
                this.on('sidebarBtnClicked', this.resume, this);

                /* creates collection of campaigns, see model for attributes */
                this.campaigns = new campaignCollection(this.campaigns, {parse: true});

                window.location.hash = ''; // for back btn hack
                return this.render();
            },

            /* render out those campaigns */
            render: function() {

                this.slurpHtml( {
                    template: template( { campaigns: this.campaigns.toJSON() } ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                this.postRender();

                return this;
            },

            /* currently, the user may only edit a campaign that is in 'draft' mode
               when more options are available, it may be best to use bootstrap's
               dropdown feature (commented out in the template)
               to allow for multiple actions to be taken on a button */
            postRender: function() {
                //will be useful when more options are needed
                //$('.dropdown-toggle').dropdown();
            },

            showNewCampaign: function() {
                /* create campaign button clicked */
                this.$el.fadeOut(400, this.showCampaignWizard.bind(this));
            },

            showEditableCampaign: function(e) {
                /* edit campaign button clicked */
                var campaignId = $(e.currentTarget).closest('*[data-js="campaignRow"]').data('id');
                this.$el.fadeOut(400, this.showCampaignWizard.bind(this, campaignId));
            },

            /* right now, we just destroy the current campaign wizard object
               if it already exists and create a new one, this is sloppy */
            showCampaignWizard: function(id) {
                var self = this;

                miniHeader.$el.hide();
                this.model.set('state', 'campaignWizard');

                // TODO: fix laziness
                if(this.campaignWizard) {
                    this.campaignWizard.remove();
                }

                /* ideally, most of these parameters should come from
                   an ajax call instead of passed through a bunch of views */ 
                this.campaignWizard = new CampaignWizard({
                    id: id,
                    howItWorksURL: this.howItWorksURL,
                    facebookPostImage: this.facebookPostImage,
                    facesExampleURL: this.facesExampleURL,
                    clientId: this.clientId,
                    token: this.token,
                    createFormAction: this.wizardCreate
                });

                /* for back btn hack */
                window.onhashchange = function () {
                    if (window.location.hash.length === 0) {
                        // we're back at the beginning
                        $('#theModal').modal('hide');
                        self.hideCampaignWizard();
                        window.onhashchange = null;
                    } else {
                        self.campaignWizard.reflectLocation();
                    }
                };
            },

            hideCampaignWizard: function () {
                this.resume();
                if (this.campaignWizard) {
                    this.campaignWizard.remove();
                }
            },

            navToCampaignSummary: function(event) {
                var campaignId = $(event.currentTarget).data('id'),
                    summaryUrl = edgeflip.router.reverse('targetadmin:campaign-summary',
                                                         this.clientId, campaignId);
                window.location = summaryUrl;
            },
           
            resume: function () {
                if (this.model.get('state') === 'mainView') return;
                this[this.model.get('state')].$el.fadeOut();
                this.model.set('state', 'mainView');
                miniHeader.$el.show();
                this.$el.fadeIn();
            }
        });
    }
);
