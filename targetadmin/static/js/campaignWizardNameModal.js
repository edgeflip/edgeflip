( function($) {
    window.campaignWizardNameModal = new ( Backbone.View.extend( {

        events: {
            'click [data-js="continueBtn"]': 'continueClicked'
        },

        initialize: function() {

            this.slurpHtml( { slurpInputs : true } );

            this.$el.on( 'shown', this.afterRender.bind(this) );
        },

        afterRender: function() {

            this.templateData.name.focus();

            this.keydownReference = this.handleKeydown.bind(this);

            this.util.document.on( 'keydown', this.keydownReference );
        },

        handleKeydown: function(e) {
           
            if( e.keyCode === 13 ) {
                e.preventDefault();
                this.templateData.continueBtn.click();
                this.util.scrollPage( 0 );
                this.util.document.off('keydown', this.keydownReference );
                this.keydownReference = undefined;
            }
        },

        continueClicked: function(e) {
            //currently, inputValidation.js validates the input
            //TODO: bring validator logic here
            this.$el.modal('hide');
        }
                
    } ) )( { el:'#campaign-name-modal' } );
} )(jQuery);
