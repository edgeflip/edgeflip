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
                'click button[data-js="createCampaignBtn"]': 'handleNewCampaign',
                'click button[data-js="editButton"]': 'handleEditCampaign',
                'click button[data-js="cloneButton"]': 'handleCloneCampaign',
                'click div[data-js="campaignName"]': 'navToCampaignSummary'
            },

            /* this view is instantiated with a list of campaigns
               (options.campaigns).  A better 
               approach would be to make this an ajax call done by
               a CampaignCollection module that defines a url attribute */
            initialize: function (options) {
                _.extend(this, options);
                this.model.set('state', 'mainView');
                this.on('sidebarSelected', this.resume, this);

                /* creates collection of campaigns, see model for attributes */
                this.campaigns = new campaignCollection(this.campaigns, {parse: true});

                this.render();
                return this;
            },

            render: function() {
                /* Render view HTML.
                 */
                this.slurpHtml({
                    template: template({ campaigns: this.campaigns.toJSON()}),
                    insertion: {$el: this.$el.appendTo(this.parentEl)}
                });
                return this;
            },

            handleNewCampaign: function () {
                /* create campaign button clicked */
                this.$el.fadeOut(400, this.showCampaignWizard.bind(this));
            },

            handleEditCampaign: function (event) {
                /* edit campaign button clicked
                 */
                this._handleWizardForCampaign(event, 'edit');
            },

            handleCloneCampaign: function (event) {
                /* clone campaign button clicked
                 */
                this._handleWizardForCampaign(event, 'clone');
            },

            _handleWizardForCampaign: function (event, action) {
                var row = $(event.currentTarget).closest('[data-js=campaignRow]'),
                    campaignId = row.data('id');

                this.$el.fadeOut(400, this.showCampaignWizard.bind(this, campaignId, action));
            },

            showCampaignWizard: function(id, action) {
                var self = this,
                    cloneId;

                if (action) {
                    if (action === 'clone') {
                        cloneId = id, id = null;
                    } else if (action !== 'edit') {
                        throw "unrecognized campaign action: " + action;
                    }
                } else if (id) {
                    throw "missing parameter: 'action'";
                }

                miniHeader.$el.hide();
                this.model.set('state', 'campaignWizard');

                if(this.campaignWizard) {
                    /* right now, we just destroy the current campaign wizard object
                     * if it already exists and create a new one, this is sloppy
                     */
                    this.campaignWizard.remove();
                }

                /* ideally, most of these parameters should come from
                   an ajax call instead of passed through a bunch of views */ 
                this.campaignWizard = new CampaignWizard({
                    id: id,
                    cloneId: cloneId,
                    howItWorksURL: this.howItWorksURL,
                    facebookPostImage: this.facebookPostImage,
                    facesExampleURL: this.facesExampleURL,
                    clientId: this.clientId,
                    token: this.token,
                });

                /* for back btn hack */
                window.onhashchange = function (event) {
                    var oldURL = event.oldURL,
                        inWizard = oldURL && oldURL.search(/#campaign\.(?:\d+\.)?wizard/) > -1;

                    if (inWizard && window.location.hash.length === 0) {
                        // we've backed out of the wizard
                        window.onhashchange = null;
                        $('#theModal').modal('hide');
                        self.hideCampaignWizard();
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

            resume: function (sidebarPrevious) {
                var hashMatch = window.location.hash.match(/^#?campaign\.(\d+)\.(clone|edit)$/),
                    campaignId,
                    action,
                    departingState;

                window.location.hash = '';

                if (hashMatch) {
                    // Request for campaign wizard subview
                    campaignId = parseInt(hashMatch[1]),
                        action = hashMatch[2];

                    this.showCampaignWizard(campaignId, action);

                } else {
                    departingState = this.model.get('state');

                    if (departingState === 'mainView') {
                        if (sidebarPrevious !== undefined) {
                            // Selection from sidebar; display container:
                            this.$el.fadeIn(200);
                        }
                        return;
                    }

                    // Resuming from subview
                    this[departingState].$el.fadeOut();
                    this.model.set('state', 'mainView');
                    miniHeader.$el.show();
                    this.$el.fadeIn();
                }
            }
        });
    }
);
