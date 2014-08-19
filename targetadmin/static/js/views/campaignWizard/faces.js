define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'templates/campaignWizard/faces',
      'css!styles/campaignWizard/faces'
    ],
    function( $, _, Backbone, template, nameTemplate ) {

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
                    template: template( {
                        name: this.model.get('name'),
                        facesExampleURL: this.facesExampleURL
                    } ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                return this;
            }

        } );
    }
);
