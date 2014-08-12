define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'templates/miniHeader',
      'css!styles/miniHeader'
    ],
    function( $, _, Backbone, template ) {

        //This module always returns the same instance of sidebar
        //Useful for accessing in other scopes
        return new ( Backbone.View.extend( {
           
            initialize: function() {
                return this;
            },

            setup: function( options ) {

                return _.extend( this, options );
            },

            render: function() {
        
                this.slurpHtml( {
                    template: template( this ),
                    insertion: { $el: this.$el.prependTo(this.parentEl) } } );

                return this;
            },

            update: function(options) {
                this.templateData.miniHeader.text( options.name );

                return this;
            }

        } ) )();
    }
);
