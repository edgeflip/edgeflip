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

                this.render();

                var self = this;

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

            /* a little sloppy -- adds content, other options for customization */
            update: function( options ) {

                var self = this;

                this.templateData.closeBtn.addClass('hide');
                this.templateData.modalHeader.removeClass('show-border');

                if( options ) {

                    /* a lot of content to display, add custom css */
                    if( options.longContent ) {
                        this.templateData.modalContainer
                            .addClass('long-content')
                            .on('hidden.bs.modal', function() {
                                self.templateData.modalContainer
                                    .off('hidden.bs.modal')
                                    .removeClass('long-content');
                            } );
                    }

                    if( options.title ) {
                        this.templateData.modalTitle.text( options.title );
                        this.templateData.modalHeader.addClass('show-border');
                    }

                    if( options.body !== undefined ) {
                        this.templateData.modalBody.html( options.body );
                    }

                    if( options.confirmText ) {
                        this.templateData.confirmBtn.text( options.confirmText );
                    }

                    if( options.showCloseBtn ) {
                        this.templateData.closeBtn.removeClass('hide');
                    }

                }

                return this;
            },

            /* fires event letting everyone know the 'confirm button was clicked */
            triggerConfirmed: function() {
                this.trigger('confirmed');
            }

        } ) )();
    }
);
