define(
    [
      'jquery',
      'vendor/underscore',
      'ourBackbone',
      'models/campaign',
      'templates/clientHome',
      'css!styles/clientHome'
    ],
    function( $, _, Backbone, campaign, template ) {

        var campaignCollection = Backbone.Collection.extend( { model: campaign } );

        return Backbone.View.extend( {
            
            model: new Backbone.Model( { } ),

            events: {
                'click button[data-js="createCampaignBtn"]': 'createCampaign'
            },

            initialize: function( options ) {

                _.extend( this, options ); 

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
                $('.dropdown-toggle').dropdown();
            },

            createCampaign: function() {
                window.location = this.createCampaignURL;
            }

        } );
    }
);
