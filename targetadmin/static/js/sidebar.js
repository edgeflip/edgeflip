define(
    [
      'jquery',
      'vendor/underscore',
      'ourBackbone',
      'templates/sidebar',
      'css!styles/sidebar'
    ],
    function( $, _, Backbone, template ) {

        return Backbone.View.extend( {
            
            model: new Backbone.Model( { state: '' } ),

            events: {
                'click li[data-js="btn"]': 'navItemClicked'
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
