define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'templates/help',
      'css!styles/help'
    ],
    function( $, _, Backbone, template ) {

        return Backbone.View.extend( {

            initialize: function( options ) {

                _.extend( this, options ); 

                return this.render();
            },

            render: function() {
                
                this.slurpHtml( {
                    template: template( this.templateOptions ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                return this;
            }
        } );
    }
);
