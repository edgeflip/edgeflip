define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/modal',
      'templates/campaignWizard/intro',
      'templates/campaignWizard/nameInput',
      'css!styles/campaignWizard/intro'
    ],
    function( $, _, Backbone, modal, template, nameTemplate ) {

        return Backbone.View.extend( {
            
            events: {
                "click button[data-js='getStartedBtn']": "promptForCampaignName"
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
            },

            promptForCampaignName: function() {
                modal.update( {
                    body: nameTemplate,
                    confirmText: 'Continue',
                  } ).on('confirmed', this.triggerNextStep, this )
                     .templateData.modalContainer.modal();
            },

            triggerNextStep: function() {
                modal.off('confirmed', this.triggerNextStep );
                this.model.set('name', modal.$el.find('input[name="name"]').val() );
                modal.templateData.modalContainer.modal('hide');
                this.trigger('nextStep');
            }

        } );
    }
);
