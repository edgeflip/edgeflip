define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'templates/campaignSummary',
      'templates/campaignSummaryFilters',
      'css!styles/campaignSummary'
    ],
    function( $, _, Backbone, template ) {

        return new ( Backbone.View.extend( {
            
            events: {
            },

            initialize: function( options ) {

                _.extend( this, options ); 

                return this.render();
            },

            render: function() {

                this.slurpHtml( {
                    template: template( { } ),
                    insertion: { $el: this.$el }
                } );

                return this;
            },

            update: function( campaignModel ) {

                console.log( campaignModel );

            }

        } ) )();
    }
)
