define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/modal',
      'templates/campaignWizard/faces',
      'css!styles/campaignWizard/faces'
    ],
    function( $, _, Backbone, modal, template, nameTemplate ) {

        return Backbone.View.extend( {
            
            events: {
            },

            initialize: function( options ) {

                _.extend( this, options ); 

                return this.render();
            },

            render: function() {

                if( this.hide ) { this.$el.hide(); }

                this.slurpHtml( {
                    template: template( this ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                return this;
            }

        } );
    }
);
