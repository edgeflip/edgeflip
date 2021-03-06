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
    function ($, _, Backbone, modal, template, nameTemplate) {

        return Backbone.View.extend({
           
            /* show modal when user clicks get started button */ 
            events: {
                "click button[data-js='getStartedBtn']": "promptForCampaignName"
            },

            /* if we are editing a campaign, show the modal that prompts for a name */
            initialize: function (options) {
                _.extend(this, options);

                this.render();

                if (this.campaignModel) {
                    this.on('shown', $.fn.click.bind(this.templateData.getStartedBtn));
                }

                return this;
            },

            render: function () {
                /* standard render may be best to have a campaign view base class for DRY */
                if (this.hide) this.$el.hide();

                this.slurpHtml({
                    template: template(this),
                    insertion: {$el: this.$el.appendTo(this.parentEl)}
                });

                return this;
            },

            promptForCampaignName: function () {
                /* Update modal content, show it.
                *  This is a little over complicated by the fact that the content
                *  is recreated every time the get started button is clicked.
                */
                modal.update({
                    body: '',
                    confirmText: 'Continue',
                }).on('confirmed', this.validateName, this)
                .templateData.modalContainer.modal();

                delete this.templateData.formInput;

                this.slurpHtml({
                    template: nameTemplate(),
                    insertion: {$el: modal.templateData.modalBody}
                });

                if (this.isEdit) this.templateData.formInput.val(this.campaignModel.get('name'));

                modal.templateData.confirmBtn.show();
            },

            validateName: function () {
                /* validate campaign name (non-empty) before we go to the next step
                 *
                 * If not valid, show error feedback.
                 *
                 * again this may be better in a base class as its done in other views, albeit differently.
                 */
                var formInput = this.templateData.formInput;

                if (formInput.val().search(/\S/) > -1) {
                    formInput.parent()
                        .removeClass('has-error')
                        .removeClass('has-feedback');
                    
                    formInput.next().addClass('hide');
                    this.goToNextStep();
                } else {
                    formInput.parent()
                        .addClass('has-error')
                        .addClass('has-feedback');
                    
                    formInput.next().removeClass('hide');
                }
            },

            goToNextStep: function () {
                /* go to the next view, whatever it is */
                this.model.set('name', modal.$el.find('input[name="name"]').val());
                this.trigger('nextStep');
            }

        });
    }
);
