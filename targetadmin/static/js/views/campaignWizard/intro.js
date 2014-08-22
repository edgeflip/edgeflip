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

                this.render();

                if( this.campaignModel ) {
                    this.on( 'shown', function() {
                        this.templateData.getStartedBtn.click();
                    }, this );
                }

                return this;
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
                    body: '',
                    confirmText: 'Continue',
                  } ).on('confirmed', this.validateName, this )
                     .templateData.modalContainer.modal();

                delete this.templateData.formInput;

                this.slurpHtml( {
                    template: nameTemplate(),
                    insertion: { $el: modal.templateData.modalBody } } );

                if( this.campaignModel ) {
                    this.templateData.formInput.val( this.campaignModel.get('name') );
                }
            },

            validateName: function() {

                if( $.trim( this.templateData.formInput.val() ) !== '' ) {

                    this.templateData.formInput.parent()
                        .removeClass('has-error')
                        .removeClass('has-feedback');
                    
                    this.templateData.formInput.next().addClass('hide');

                    this.goToNextStep();

                } else {
                    this.templateData.formInput.parent()
                        .addClass('has-error')
                        .addClass('has-feedback');
                    
                    this.templateData.formInput.next().removeClass('hide');
                }
            },

            goToNextStep: function() {
                modal.off('confirmed', this.triggerNextStep );
                this.model.set('name', modal.$el.find('input[name="name"]').val() );
                modal.templateData.modalContainer.modal('hide');
                this.trigger('nextStep');
            }

        } );
    }
);
