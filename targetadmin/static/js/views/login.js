define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'templates/login',
      'css!styles/login'
    ],
    function( $, _, Backbone, template ) {

        return Backbone.View.extend( {
           
            events: {
            },

            initialize: function( options ) {

                _.extend( this, options );

                return this.render();
            },

            render: function() {

                this.slurpHtml( {
                    template: template( this ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                if( this.error ) {
                    this.templateData.inputContainer.addClass('has-feedback has-error');
                    this.templateData.errorFeedback.removeClass('hide');
                }

                return this;
            }

        } );
    }
);
