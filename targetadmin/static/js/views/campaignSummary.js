/* module for campaign summary view */
define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'models/campaign',
      'templates/campaignSummary',
      'css!styles/campaignSummary'
    ],
    function( $, _, Backbone, campaign, template ) {

        return Backbone.View.extend( {
            /* model for view's state */
            model: new Backbone.Model( { } ),

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
