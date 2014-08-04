define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'models/campaign', // model for campaign
      'templates/clientCampaigns', // function which returns campaign list html
      'css!styles/clientCampaigns' // CSS ( inserted into DOM )
    ],
    function( $, _, Backbone, campaign, template ) {

        var campaignCollection = Backbone.Collection.extend( { model: campaign } );

        return Backbone.View.extend( {
            
            model: new Backbone.Model( { } ),

            /* jquery event handler: function */ 
            events: {
                'click button[data-js="createCampaignBtn"]': 'createCampaign',
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
            createCampaign: function() {
                window.location = this.createCampaignURL;
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
