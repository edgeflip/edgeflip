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
                'click button[data-js="confirmBtn"]': 'triggerConfirmed'
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

                var self = this;
                        
                this.templateData.closeBtn.addClass('hide');
                this.templateData.modalHeader.removeClass('show-border');

                if( options ) {

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

            triggerConfirmed: function() {
                this.trigger('confirmed');
            }

        } ) )();
    }
);
