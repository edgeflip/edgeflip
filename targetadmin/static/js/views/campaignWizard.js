define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/modal',
      'templates/campaignWizard/intro',
      'templates/campaignWizard/nameInput',
      'css!styles/campaignWizard'
    ],
    function( $, _, Backbone, modal, introTemplate, nameTemplate ) {

        return Backbone.View.extend( {
            
            model: new Backbone.Model( { } ),

            events: {
                "click button[data-js='getStartedBtn']": "promptForCampaignName"
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
            },

            promptForCampaignName: function() {
                modal.update( {
                    body: nameTemplate,
                    confirmText: 'Continue'
                } );
                modal.templateData.modalContainer.modal();
            }

        } );
    }
);
