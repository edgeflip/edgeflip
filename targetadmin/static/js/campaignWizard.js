$( function() {    

    window.campaignWizard = new ( Backbone.View.extend( {

        initialize: function() {

            $('i.icon-question-sign').popover( { trigger: 'hover' } );
        }

    } ) )( { el: '#wizard-form' } );


    // "Steps"
    $('.step-submit').click(function(e) {
        var step = $(this).data('step');
        
        $('.wizard-step').hide();

        $('#' + step).show();
        
        if( step === 'faces' && (! window.facesImageCompanion.model.get('hasRendered') ) ) {
            window.facesImageCompanion.afterRender();
        }
        
        if( step === 'fbobjects' && (! window.fbObjImageCompanion.model.get('hasRendered') ) ) {
            window.fbObjImageCompanion.afterRender();
        }

        if( step === 'intro' ) {
            $('#intro-header').fadeIn();    
            $('.campaign-name').addClass('hide');
        } else {
            $('#intro-header').fadeOut();    
            $('.campaign-name').removeClass('hide');
        }

        if( $(this).attr('id') === 'step1-next' ) {
            $('.campaign-name span').text( $('#id_name').val() );
        }

        $('body,html').scrollTop( 0 );
    } );

} );
