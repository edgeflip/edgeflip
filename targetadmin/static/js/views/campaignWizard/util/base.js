define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
    ], function( $, _, Backbone, windowUtil ) {
     
        return Backbone.View.extend( {

            // when validation is more nuanced, it may be better to move them to
            // the campaign wizard model 
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
