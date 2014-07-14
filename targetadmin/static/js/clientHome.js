define(
    [
      'jquery',
      'vendor/underscore',
      'ourBackbone',
      'templates/clientHome',
      'css!styles/clientHome'
    ],
    function( $, _, Backbone, template ) {

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
                    template: template( this.templateOptions ),
                    insertion: { $el: this.parentEl } } );

                return this;
            }
        } );
    }
);
