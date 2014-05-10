$( function() {

    var errorPopovers = [ $('.invalid-input-popover') ],
        config = {
            rightOffset: 5,
            popoverOpts: {
                animation: false,
                trigger: 'manual',
                content: function() { return popoverText; },
                placement: 'right'
            }
        },
        isEmpty = function( val ) { return ( $.trim( val ) === '' ); },
        popoverText = undefined,
        getPopoverClone = function() { 
            var clone = errorPopovers[0].clone()
                .before(errorPopovers[0])
                .popover( config.popoverOpts )
            errorPopovers.push( clone );
            return clone;
        },

        positionAndShowPopover = function( popover, meta ) {
            popoverText = meta.invalidText;
            popover.css( {
                top: meta.el.offset().top + ( meta.el.outerHeight( true ) / 2 ),
                left: meta.el.offset().left + meta.el.outerWidth( true ) + config.rightOffset } ).popover('show');
            popover.next().on( 'click', function() { popover.popover('hide'); } );
        },
        handleInvalidField = function(meta) {
            var unusedPopover = _.find( errorPopovers, function( el ) { return el.children().length === 0 } );

            if( unusedPopover === undefined ) {
                unusedPopover = getPopoverClone();
            }
       
            positionAndShowPopover( unusedPopover, meta );
        },
        validators = [
            {
                triggerEl: $('#step1-next'),
                event: 'click',
                inputs: [
                    { el: $('#id_name'),
                      isValid: function( el ) { return ( isEmpty( el.val() ) === false ) },
                      invalidText: 'We do require a name.'
                    }

                ]
            }
        ];

    //instantiate img popover
    errorPopovers[0]
        .popover( config.popoverOpts )
        
    _.each( validators, function( validator ) {
        validator.triggerEl.on( validator.event, function(e) {
            _.each( validator.inputs, function( meta ) {
                 if( ! meta.isValid( meta.el ) ) {
                     e.stopImmediatePropagation();
                     handleInvalidField(meta);
                 }
            } );
        } );
    } );
} );
