define(
    [ 'jquery', 'vendor/underscore', 'ourBackbone', util ],

    function( $, _, Backbone, util ) {

        return new ( Backbone.View.extend( {

            elements: [ ],

            config: {

                offsets: {
                    right: 5,
                    bottom: 5
                }

            },

            initialize: function() {

                this.elements.push(
                    $('<div class="invalid-input-popover"></div>')
                        .popover( this.getPopoverOptions() ) );

                return this;
            },

            render: function() {
                this.$el.append( this.elements[0] ); 
                return this;
            },

            getPopoverOptions: function() {
                var self = this;

                return {
                    animation: false,
                    trigger: 'manual',
                    content: function() { self.getPopoverText() },
                    placement: 'bottom'
                }
            },

            getNewPopover: function() { 
                var clone = this.elements[0].clone()
                    .insertBefore(this.elements[0])
                    .popover( config.popoverOpts );

                errorPopovers.push( clone );
                return clone;
            },

            positionAndShowPopover = function() {
                var el = this.currentModel.get('el'),
                    offset = el.offset(),
                    top = offset.top + ( el.outerHeight( true ) / 2 ),
                    left = offset.left + ( el.outerWidth( true ) / 2 );

                this.currentPopover.css( { top: top, left: left } ).popover('show');

                this.currentPopover.next().addClass('invalid-input-message').on( 'click', function() {
                    this.currentModel.set('popoverEl', undefined );
                    this.currentPopover.popover('hide');
                } );

                el.on( 'focus', function() {
                    this.currentModel.set('popoverEl', undefined );
                    this.currentPopover.popover('hide');
                } );

                this.currentModel.set('popoverEl', popover );
            },

            notifyUser = function( model ) {
                this.currentModel = model;
                this.currentPopover = _.find( this.elements, function( el ) { return !el.next().hasClass('popover') } );

                if( this.currentPopover === undefined ) {
                    this.currentPopover = this.getNewPopover();
                }
           
                positionAndShowPopover();
            },
       

        } ) )( { el: 'body' } );
    }
);
/*
$( function() {

    var errorPopovers = [ $('.invalid-input-popover') ],
        maxScroll,
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
                      doNotDisplay: true
                    }
                ]
            },
            {
                triggerEl: $('#step3-next'),
                resetEl: $('#step3-prev'),
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
                resetEl: $('#step4-prev'),
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

    //we want to scroll to the top most invalid input field
    //but if we don't need to scroll, we shouldn't
    maxScroll = $('body').height() - $(window).height();
    $(window).on('resize', function() {
        maxScroll = $('body').height() - $(window).height();
    } );

    //instantiate img popover
    errorPopovers[0]
        .popover( config.popoverOpts )
        
    _.each( validators, function( validator ) {

        //hide invalid inputs on "previous" button click
        if( validator.resetEl ) {
            validator.resetEl.on( 'click', function(e) {
                _.each( validator.inputs, function( inputModel ) {
                    if( inputModel.popoverEl !== undefined ) {
                         inputModel.popoverEl.popover('hide');
                         inputModel.popoverEl = undefined;
                     }
                } );
            } );
        }

        validator.triggerEl.on( validator.event, function(e) {
            //prevent scroll to top of page
            e.preventDefault();
            var atleastOneInvalid = false;
            _.each( validator.inputs, function( inputModel ) {
                var isValid = isElValid( inputModel.el );

                 if( isValid ) {
                     if( inputModel.popoverEl !== undefined ) {
                         inputModel.popoverEl.popover('hide');
                         inputModel.popoverEl = undefined;
                     }
                 } else {
                     e.stopImmediatePropagation();
                     if( inputModel.doNotDisplay === true ) { return; }

                     atleastOneInvalid = true;
                     if( inputModel.popoverEl === undefined ) {
                         notifyUser(inputModel);
                     }
                 }
            } );

            if( atleastOneInvalid ) {

                var indexOfFirstInvalidEl = 0,
                    scrollTop = undefined;
                
                _.find( validator.inputs, function( inputModel ) {
                    if( inputModel.popoverEl !== undefined ) {
                        //el.next().hasClass('popover') ) {
                        return true;
                    }
                    indexOfFirstInvalidEl++;
                } );

                scrollTop = validator.inputs[indexOfFirstInvalidEl].el.offset().top - 100;

                if( scrollTop < maxScroll ) {
                    $('html,body').animate(
                        { 'scrollTop': scrollTop },
                        { duration: 600 } );
                }

            } else if( validator.triggerEl.attr('id') === 'wizard-submit' ) {
                $('#wizard-form').submit();
            }
        } );
    } );
} );
*/
