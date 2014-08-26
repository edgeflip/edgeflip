/* campaign wizard's intro sub view model */
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
           
            /* show modal when user clicks get started button */ 
            events: {
                "click button[data-js='getStartedBtn']": "promptForCampaignName"
            },

            /* if we are editing a campaign, show the modal that prompts for a name */
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

            /* standard render, may be best to have a campaign view base class for DRY */
            render: function() {

                if( this.hide ) { this.$el.hide(); }

                this.slurpHtml( {
                    template: template( this ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                return this;
            },

            /* update modal content, show it.  This is a little over
               complicated by the fact that the content is recreated every time
               the get started button is clicked. */
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

            /* before we go to the next step, make sure we have a valid campaign
               name ( non empty ), again this may be better in a base class as its
               done in other views, albeit differently.  If not valid, show error
               feedback. */
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

            /* go to the next view, whatever it is */
            goToNextStep: function() {
                modal.off('confirmed', this.triggerNextStep ); // don't need this anymore
                this.model.set('name', modal.$el.find('input[name="name"]').val() );
                modal.templateData.modalContainer.modal('hide');
                this.trigger('nextStep');
            }

        } );
    }
);
