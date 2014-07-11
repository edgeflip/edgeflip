define(
    [
      'jquery',
      'vendor/underscore',
      'ourBackbone',
      'templates/sidebar',
      'css!styles/sidebar'
    ],
    function( $, _, Backbone, template ) {

        return new ( Backbone.View.extend( {
            
            model: new Backbone.Model( { state: '' } ),

            events: {
                'click li[data-js="btn"]': 'navItemClicked'
            },

            initialize: function() {

                this.parentEl = $("#content-container");

                return this.render();
            },

            render: function() {

                this.slurpHtml( {
                    template: template( {
                        logoSrc:
                        clientName:
                    } ),
                    insertion: { $el: this.parentEl } );

                return this;
            }

    } ) )();
);
