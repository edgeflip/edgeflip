/* Module that exports a campaign wizard base view, should have
   more added to it */
define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
    ], function( $, _, Backbone, windowUtil ) {
     
        return Backbone.View.extend( {

            /* when validation is more nuanced, it may be better to move them to
               a campaign wizard model, see backbone model documentation,
               it looks at all templateData formInputs that don't have
               'data-type' attrbutes that are no of "optional" value, and makes
               sure they aren't empty, if they are, add bootstrap error stuff */
            validateInputs: function() {
                
                var allValid = true,
                    firstInvalidEl = undefined;

                _.each( this.templateData.formInput, function( el ) {
                    var el = $(el);

                    if( el.attr('data-type') !== 'optional' ) {

                        if( $.trim( el.val() ) === '' ) {
                            if( allValid ) { firstInvalidEl = el; }
                            allValid = false; 
                            el.parent()
                                .addClass('has-error')
                                .addClass('has-feedback');
                            el.next().removeClass('hide');
                        } else {
                            el.parent()
                                .removeClass('has-error')
                                .removeClass('has-feedback');
                            
                            el.next().addClass('hide');
                        }
                   }
                }, this );

                if( allValid ) {
                    this.trigger('validated');
                } else {
                    $('html,body').animate( {
                        'scrollTop': firstInvalidEl.offset().top - 50
                    } );
                }

                return this;
            }
    } );
} );
