/* module for campaign summary view */
define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'models/campaign',
      'views/campaignWizard/skeleton',
      'templates/campaignSummary',
      'css!styles/campaignSummary'
    ],
    function( $, _, Backbone, campaign, CampaignWizard, template ) {

        return Backbone.View.extend( {
            /* model for view's state */
            model: new Backbone.Model( { } ),

            /* see sidebar.js for not bloated DOM suggestion */
            events: {
                'click button[data-js="createCampaignBtn"]': 'showNewCampaign',
                'click button[data-js="editButton"]': 'showEditableCampaign',
                'click div[data-js="contentBtn"]': 'showCampaignList',
            },

            initialize: function( options ) {

                _.extend( this, options );

                this.model.set( 'state', 'mainView' );

                /* creates campaign, see model for attributes */
                this.campaign = new campaign(
                    options,
                    { parse: true }
                );

                return this.render();
            },

            /* create campaign button clicked */
            showNewCampaign: function() {
                this.$el.fadeOut( 400, this.showCampaignWizard.bind(this) );
            },

            /* edit campaign button clicked */
            showEditableCampaign: function(e) {
                this.$el.fadeOut( 400, this.showCampaignWizard.bind( this, this.campaign.id ) );
            },

            /* right now, we just destroy the current campaign wizard object
               if it already exists and create a new one, this is sloppy */
            showCampaignWizard: function( id ) {

                this.model.set( 'state', 'campaignWizard' );

                // TODO: fix laziness
                if( this.campaignWizard ) {
                    this.campaignWizard.remove();
                }
               
                /* ideally, most of these parameters should come from
                   an ajax call instead of passed through a bunch of views */ 
                this.campaignWizard =
                    new CampaignWizard( {
                        id: id,
                        howItWorksURL: this.howItWorksURL,
                        facebookPostImage: this.facebookPostImage,
                        facesExampleURL: this.facesExampleURL,
                        clientId: this.clientId,
                        token: this.token,
                        formAction: this.formAction,
                        campaignDataURL: this.campaignDataURL
                } );
            },

            /* render out that campaign */
            render: function() {

                this.slurpHtml( {
                    template: template( { campaign: this.campaign.toJSON() } ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                return this;
            },

        } );
    }
);
