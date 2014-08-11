define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'templates/campaignWizard/intro',
      'css!styles/campaignWizard'
    ],
    function( $, _, Backbone, CampaignWizard, campaign, template ) {

        var campaignCollection = Backbone.Collection.extend( { model: campaign } );

        return Backbone.View.extend( {
            
            model: new Backbone.Model( { } ),

            /* jquery event handler: function */ 
            events: {
                'click button[data-js="createCampaignBtn"]': 'showCampaignWizard',
                'click button[data-js="editButton"]': 'navToEditCampaign',
                'click div[data-js="campaignName"]': 'navToCampaignSummary'
            },

            /* called on instantiation */
            initialize: function( options ) {

                _.extend( this, options ); 

                /* creates collection of campaigns, see model for attributes */
                this.campaigns = new campaignCollection(
                    this.campaigns,
                    { parse: true } );

                return this.render();
            },

            render: function() {

                this.slurpHtml( {
                    template: template( { campaigns: this.campaigns.toJSON() } ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                this.postRender();

                return this;
            },

            postRender: function() {
                //will be useful when more options are needed
                //$('.dropdown-toggle').dropdown();
            },

            /* create campaign button clicked */
            showCampaignWizard: function() {
                var self = this;
                this.$el.fadeOut( 400, function() {
                    self.campaignWizard = new CampaignWizard();
                } );
            },

            /* campaign name clicked */
            navToCampaignSummary: function(e) {
                window.location = this.campaignSummaryURL.replace("0", $(e.currentTarget).data('id') );
            },
            
            /* campaign name clicked */
            navToEditCampaign: function(e) {
                window.location = this.createCampaignURL + $(e.currentTarget).closest('div[data-js="campaignRow"]').data('id');
            }

        } );
    }
);
