$( function() {

    var errorPopovers = [ $('.invalid-input-popover') ],
        config = {
            rightOffset: 5,
            bottomOffset: 5,
            popoverOpts: {
                animation: false,
                trigger: 'manual',
                //TODO: figure out why these are called twice
                content: function() { return popoverText; },
                placement: function() { return placement; }
            }
        },
        isEmpty = function( val ) { return ( $.trim( val ) === '' ); },
        isElValid = function( el ) { return ( isEmpty( el.val() ) === false ) },
        popoverText = undefined,
        placement = undefined,
        makeInputModel = function( opts ) {
            return  {
                el: $( opts.id ),
                invalidText: ( opts.text ) ? opts.text : 'Required field.',
                placement: ( opts.placement ) ? opts.placement :'bottom',
                popoverEl: undefined
            }
        },
        getPopoverClone = function() { 
            var clone = errorPopovers[0].clone()
                .insertBefore(errorPopovers[0])
                .popover( config.popoverOpts );

            errorPopovers.push( clone );
            return clone;
        },

        positionAndShowPopover = function( popover, inputModel ) {
            var top, left;

            placement = inputModel.placement,
            popoverText = inputModel.invalidText;

            if( placement === 'right' ) {
                top = inputModel.el.offset().top + ( inputModel.el.outerHeight( true ) / 2 );
                left = inputModel.el.offset().left + inputModel.el.outerWidth( true ) + config.rightOffset;
            } else if( placement === 'bottom' ) {
                top = inputModel.el.offset().top + ( inputModel.el.outerHeight( true ) / 2 );
                left = inputModel.el.offset().left + ( inputModel.el.outerWidth( true ) / 2 );
            }

            popover.css( { top: top, left: left } ).popover('show');

            popover.next().addClass('invalid-input-message').on( 'click', function() {
                inputModel.popoverEl = undefined;
                popover.popover('hide');
            } );

            inputModel.el.on( 'focus', function() {
                inputModel.popoverEl = undefined;
                popover.popover('hide');
            } );

            inputModel.popoverEl = popover;
        },
        notifyUser = function(inputModel) {
            var unusedPopover = _.find( errorPopovers, function( el ) { return !el.next().hasClass('popover') } );

            if( unusedPopover === undefined ) {
                unusedPopover = getPopoverClone();
            }
       
            positionAndShowPopover( unusedPopover, inputModel );
        },
        validators = [
            {
                triggerEl: $('#step1-next'),
                event: 'click',
                inputs: [
                    { el: $('#id_name'),
                      invalidText: 'A name is required.',
                      placement: 'right',
                      popoverEl: undefined
                    }

                ]
            },
            {
                triggerEl: $('#step3-next'),
                event: 'click',
                inputs: [
                    { el: $('#id_sharing_prompt'),
                      invalidText: 'A headline is required.',
                      placement: 'bottom',
                      popoverEl: undefined
                    },
                    { el: $('#id_thanks_url'),
                      invalidText: 'A thanks URL is required.',
                      placement: 'bottom',
                      popoverEl: undefined
                    },
                    { el: $('#id_error_url'),
                      invalidText: 'An error URL is required.',
                      placement: 'bottom',
                      popoverEl: undefined
                    }

                ]
            },
            {
                triggerEl: $('#wizard-submit'),
                event: 'click',
                inputs: _.map( [
                    { id: '#id_org_name' },
                    { id: '#id_og_title' },
                    { id: '#id_og_image' },
                    { id: '#id_og_description' },
                    { id: '#id_content_url' }
                  ], makeInputModel )
            }
        ];

    //instantiate img popover
    errorPopovers[0]
        .popover( config.popoverOpts )
        
    _.each( validators, function( validator ) {
        validator.triggerEl.on( validator.event, function(e) {
            var atleastOneInvalid = false;
            _.each( validator.inputs, function( inputModel ) {
                var isValid = isElValid( inputModel.el );

                 if( isValid ) {
                     if( inputModel.popoverEl !== undefined ) {
                         inputModel.popoverEl.popover('hide');
                         inputModel.popoverEl = undefined;
                     }
                 } else {
                     atleastOneInvalid = true;
                     e.stopImmediatePropagation();
                     if( inputModel.popoverEl === undefined ) {
                         notifyUser(inputModel);
                     }
                 }
            } );

            if( atleastOneInvalid ) {

                var indexOfFirstInvalidEl = 0;
                
                _.find( errorPopovers, function( el ) {
                    if( el.next().hasClass('popover') ) {
                        return true;
                    }
                    indexOfFirstInvalidEl++;
                } );

                $('html,body').animate(
                    { 'scrollTop': validator.inputs[indexOfFirstInvalidEl].el.offset().top - 100 },
                    { duration: 600 } );

            } else if( validator.triggerEl.attr('id') === 'wizard-submit' ) {
                $('#wizard-form').submit();
            }
        } );
    } );
} );
