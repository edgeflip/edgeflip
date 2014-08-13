define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'templates/modal',
      'css!styles/modal'
    ],
    function( $, _, Backbone, template ) {

        //Singleton pattern
        return new ( Backbone.View.extend( {
           
            events: {
            },

            initialize: function() {

                this.render();

                return this;
            },

            render: function() {

                this.slurpHtml( {
                    template: template(),
                    insertion: { $el: this.$el.appendTo($('body')) } } );

                return this;
            },

            update: function( options ) {

                if( options && options.body ) {
                    this.templateData.modalBody.html( options.body );
                }

                if( options && options.confirmText ) {
                    this.templateData.confirmBtn.text( options.confirmText );
                }
            }

        } ) )();
    }
);
