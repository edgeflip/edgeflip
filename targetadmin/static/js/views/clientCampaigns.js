define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/campaignWizard/skeleton',
      'views/miniHeader',
      'models/campaign', // model for campaign
      'templates/clientCampaigns', // function which returns campaign list html
      'css!styles/clientCampaigns' // CSS ( inserted into DOM )
    ],
    function( $, _, Backbone, CampaignWizard, miniHeader, campaign, template ) {

        var campaignCollection = Backbone.Collection.extend( { model: campaign } );

        return Backbone.View.extend( {
            
            model: new Backbone.Model( { } ),

            /* jquery event handler: function */ 
            events: {
                'click button[data-js="createCampaignBtn"]': 'showNewCampaign',
                'click button[data-js="editButton"]': 'showEditableCampaign',
                'click div[data-js="campaignName"]': 'navToCampaignSummary'
            },

            /* called on instantiation */
            initialize: function( options ) {

                _.extend( this, options );

                this.model.set( 'state', 'mainView' );
                this.on( 'sidebarBtnClicked', this.handleSidebarClick, this );

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
            showNewCampaign: function() {
                this.$el.fadeOut( 400, this.showCampaignWizard.bind(this) );
            },

            showEditableCampaign: function(e) {
                var campaignId = $(e.currentTarget).closest('*[data-js="campaignRow"]').data('id');
                this.$el.fadeOut( 400, this.showCampaignWizard.bind( this, campaignId ) );
            },

            showCampaignWizard: function( id ) {

                miniHeader.$el.hide();
                this.model.set( 'state', 'campaignWizard' );

                // TODO: fix laziness
                if( this.campaignWizard ) {
                    this.campaignWizard.remove();
                }
                
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

            /* campaign name clicked */
            navToCampaignSummary: function(e) {
                window.location = this.campaignSummaryURL.replace("0", $(e.currentTarget).data('id') );
            },
            
            /* campaign name clicked */
            navToEditCampaign: function(e) {
                window.location = this.createCampaignURL + $(e.currentTarget).closest('div[data-js="campaignRow"]').data('id');
            },

            handleSidebarClick: function() {
                if( this.model.get('state') !== 'mainView' ) {
                    this[ this.model.get('state') ].$el.fadeOut();
                    this.model.set( 'state', 'mainView' );
                    miniHeader.$el.show();
                    this.$el.fadeIn();
                }
            }

        } );
    }
);
