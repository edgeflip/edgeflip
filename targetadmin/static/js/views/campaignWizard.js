define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'templates/campaignWizard/intro',
      'css!styles/campaignWizard'
    ],
    function( $, _, Backbone, introTemplate ) {

        return Backbone.View.extend( {
            
            model: new Backbone.Model( { } ),

            events: {
            },

            initialize: function( options ) {

                _.extend( this, options ); 

                return this.render();
            },

            render: function() {

                this.slurpHtml( {
                    template: introTemplate( this ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                return this;
            }

        } );
    }
);
