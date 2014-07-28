define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'templates/campaignSummary',
      'css!styles/campaignSummary'
    ],
    function( $, _, Backbone, template ) {

        return Backbone.View.extend( {
            
            events: {
            },

            initialize: function( options ) {

                _.extend( this, options ); 

                return this.render();
            },

            render: function() {

                this.slurpHtml( {
                    template: template( { } ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                return this;
            }

        } );
    }
);
