/* Module implementing bootstrap's modal dialog.
   See bootstrap 3.1.1 documentation for more details */
define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'templates/modal',
      'css!styles/modal'
    ],
    function( $, _, Backbone, template ) {

        /* Singleton pattern, every define([ 'views/modal'[) will return this object */
        return new ( Backbone.View.extend( {
          
            /* confirm button clicked calls triggerConfirmed method */ 
            events: {
                'click button[data-js="confirmBtn"]': 'triggerConfirmed'
            },

            initialize: function() {
                var self = this;

                this.render();

                this.templateData.modalContainer.on('confirm_bad', function() {
                    self.templateData.confirmBtn.prop("disabled", true);
                });

                this.templateData.modalContainer.on('confirm_ok', function() {
                    self.templateData.confirmBtn.prop("disabled", false);
                });

                return this;
            },

            /* places template in DOM */
            render: function() {
                this.slurpHtml( {
                    template: template(),
                    insertion: { $el: this.$el.appendTo($('body')) } } );
                return this;
            },

            update: function (options) {
                var self = this;
                _.defaults(options, {
                    title: '',
                    body: '',
                    confirmText: ''
                });

                this.templateData.closeBtn.addClass('hide');
                this.templateData.modalHeader.removeClass('show-border');

                /* a lot of content to display, add custom css */
                if (options.longContent) {
                    this.templateData.modalContainer
                        .addClass('long-content')
                        .on('hidden.bs.modal', function() {
                            self.templateData.modalContainer
                                .off('hidden.bs.modal')
                                .removeClass('long-content');
                        });
                }

                this.templateData.modalTitle.text(options.title);
                this.templateData.modalHeader.toggleClass('show-border', !!options.title);
                this.templateData.modalBody.html(options.body);
                this.templateData.confirmBtn.text(options.confirmText);
                this.templateData.closeBtn.toggleClass('hide', !options.showCloseBtn);

                this.templateData.modalContainer.trigger('confirm_ok');

                return this;
            },

            /* fires event letting everyone know the 'confirm button was clicked */
            triggerConfirmed: function() {
                this.trigger('confirmed');
            }

        } ) )();
    }
);
