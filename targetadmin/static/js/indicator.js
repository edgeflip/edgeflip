define(
    [
      'jquery',
      'vendor/underscore',
      'ourBackbone',
      'util',
      'inputValidator'
    ],

    function( $, _, Backbone, util, inputValidator ) {

        return Backbone.View.extend( {

            events: {
                'focus input,textarea': 'fieldFocused',
                'blur input,textarea': 'fieldBlurred',
                'click button[data-js="nextBtn"]': 'nextClicked',
                'click button[data-js="prevBtn"]': 'prevClicked'
            },

            initialize: function( options ) {
                var self = this;

                this.slurpHtml( { slurpInputs: true } );

                $.extend( this, options );

                this.config = {
                    verticalImagePadding: 10
                };

                this.model = new Backbone.Model( {
                    currentField: undefined,
                    imageContainerTop: undefined,
                    imageContainerLeft: undefined,
                    imageContainerHeight: undefined,
                    inputContainerHeight: 0,
                    inputContainerTop: undefined,
                    inputContainerLeft: undefined,
                    originalImageHeight: undefined,
                    originalImageWidth: undefined,
                    multiplierY: undefined,
                    multiplierX: undefined
                } );
                
                util.computeSizes();

                this.getImageDimensions();

                this.templateData.imagePopover.popover( {
                    animation: false,
                    trigger: 'manual',
                    content: function() { return self.getPopoverText(); },
                    placement: function() { return self.getPopoverPlacement(); }
                } );

                this.templateData.inputPopover.popover( {
                    animation: false,
                    trigger: 'manual',
                    content: function() { return self.getPopoverText(); },
                    placement: 'right'
                } );

                this.delegateWindowEvents();
            },

            getImageDimensions: function() {
                var self = this;

                if( this.templateData.image.height() ) {
                    this.setImageDimensions();
                } else {
                    this.templateData.image.on( 'load', 
                        function() { self.setImageDimensions() } );
                }
            },

            shown: function() {
                $('body,html').scrollTop( 0 );

                this.getImageDimensions();
            },

            setImageDimensions: function() {
                this.model.set( {
                    originalImageHeight: this.templateData.image.height(),
                    originalImageWidth: this.templateData.image.width()
                } );

                this.templateData.image.addClass( 'indicator-image' );

                this.afterImageLoad();
            },

            afterImageLoad: function() {

                this.storeElementDimensions();

                this.templateData.imageContainer.height( this.model.get('imageContainerHeight') );

                this.sizeAndPositionImage();
                
                util.computeSizes();
            },

            storeElementDimensions: function() {
                var imageContainerOffset = this.templateData.imageContainer.offset(),
                    inputContainerOffset = this.templateData.inputContainer.offset();

                this.model.set( {
                    imageContainerTop: imageContainerOffset.top,
                    imageContainerLeft: imageContainerOffset.left,
                    inputContainerTop: inputContainerOffset.top,
                    inputContainerLeft: inputContainerOffset.left,
                    inputContainerHeight: this.templateData.inputContainer.outerHeight( true ),
                } );

                this.model.set( 'imageContainerHeight', 
                    util.windowHeight -
                    this.model.get('imageContainerTop') -
                    this.config.verticalImagePadding );

                this.listenTo( this.model, 'change:imageContainerHeight', this.checkMaxImageHeight );
            },

            checkMaxImageHeight: function() {
                if( this.model.get('imageContainerHeight') > this.model.get('inputContainerHeight') ) {
                    this.model.set('imageContainerHeight', this.model.get('inputContainerHeight') );
                }
            },

            sizeAndPositionImage: function() {

                var diff = this.model.get('inputContainerTop') - util.scrollTop,
                    top = 0,
                    stickyHeaderBump = 0,
                    self = this;

                //if the viewport contains the top of the input container
                if( diff > 0 ) {

                    if( diff < util.navbarHeight ) { stickyHeaderBump = util.navbarHeight - diff; }

                    this.model.set( 'imageContainerHeight',
                        util.windowHeight - diff - this.config.verticalImagePadding - stickyHeaderBump );
                
                    top = stickyHeaderBump;

                //if the viewport contains only our form fields and our image
                } else if( ( util.scrollTop + util.windowHeight ) <
                           ( this.model.get('inputContainerHeight') + this.model.get('inputContainerTop') ) ) {
                    
                    this.model.set( 'imageContainerHeight',
                        this.windowHeight - util.navbarHeight - ( this.verticalImagePadding * 2 ) );

                    top = ( util.scrollTop - this.model.get('inputContainerTop') ) +
                          util.navbarHeight + this.config.verticalImagePadding;
                
                //if the viewport contains the bottom of the input container
                } else {

                    this.model.set( 'imageContainerHeight', 
                        ( this.model.get('inputContainerHeight') + this.model.get('inputContainerTop') - util.scrollTop ) -
                        ( util.navbarHeight + this.config.verticalImagePadding ) );

                    top = util.scrollTop - this.model.get('inputContainerTop') +
                          util.navbarHeight + this.config.verticalImagePadding;
                }

                this.templateData.imageContainer.animate(
                    { top: top, height: this.model.get('imageContainerHeight') },
                    { duration: 200,
                      complete: function() {
                        self.setImageMetaData();
                        if( self.model.get('currentField') ) { self.positionAndShowPopover(); }
                      } } );
        
                return this;
            },

            setImageMetaData: function() {

                //TODO: should use image container values
                this.model.set( {
                    imageWidth: this.templateData.image.outerWidth(true),
                    imageHeight: this.templateData.image.outerHeight(true)
                } );

                this.model.set( {
                    multiplierX: this.model.get('imageWidth') / this.model.get('originalImageWidth'),
                    multiplierY: this.model.get('imageHeight') / this.model.get('originalImageHeight')
                } );

                return this;
            },

            positionAndShowPopover: function() {

                var currentField = this.fields[ this.model.get('currentField') ];
                    inputEl = undefined,
                    inputOffset = undefined;

                if( currentField.indicator.get('coords') ) {

                    this.templateData.inputPopover.popover('hide');
                    this.templateData.imagePopover.css( {
                        top: currentField.indicator.get('coords').y * this.model.get('multiplierY'),
                        left: currentField.indicator.get('coords').x * this.model.get('multiplierX') } ).popover('show');

                } else {

                    this.templateData.imagePopover.popover('hide');

                    inputEl = this.templateData[ this.model.get('currentField') ];
                    inputOffset = inputEl.position();

                    this.templateData.inputPopover.css( {
                        top: inputOffset.top + ( inputEl.outerHeight( true ) / 2 ),
                        left: inputOffset.left + inputEl.outerWidth( true ) + 5 } ).popover('show');
                }

                return this;
            },
    
            fieldFocused: function(e) {
                this.model.set( 'currentField', $(e.currentTarget).attr('name') );
                this.scrollToField();
            },
            
            fieldBlurred: function(e) {
                this.hidePopover();
                this.model.set( 'currentField', null );
            },

            delegateWindowEvents: function() {
                var self = this;

                //handle window resize so our popovers and images look alright
                util.window.resize( function() { self.handleWindowResize(); } );
                util.window.scroll( _.debounce( function() { self.sizeAndPositionImage() }, 300 ) );
            },

            handleWindowResize: function() {
                this.model.set( {
                    imageContainerHeight: util.windowHeight - this.model.get('imageContainerTop') - this.config.verticalImagePadding } );

                this.templateData.imageContainer.height( this.model.get('imageContainerHeight') );
                this.sizeAndPositionImage();
            },

            hidePopover: function() {
                if( this.fields[ this.model.get('currentField') ].indicator.get('coords') ) {
                    this.templateData.imagePopover.popover('hide');
                } else {
                    this.templateData.inputPopover.popover('hide');
                }

                return this;
            },

            scrollToField: function() {

                var self = this,
                    formElTop = this.templateData[ this.model.get('currentField') ].offset().top,
                    scrollTop = ( formElTop - ( util.windowHeight / 2 ) ),
                    maxDifference = this.model.get('inputContainerHeight') - this.model.get('imageContainerHeight'),
                    difference = formElTop -
                        ( ( this.model.get('imageContainerTop') - parseFloat( this.templateData.imageContainer.css('top' ) ) )
                            + ( this.model.get('imageHeight') / 2 ) );

                if( difference < 0 ) { difference = 0; }
                else if( difference > maxDifference ) { difference = maxDifference; }

                this.templateData.imageContainer.animate(
                    { 'top': difference },
                    { complete: function() {
                        var offset = self.templateData.imageContainer.offset()
                        self.model.set( {
                            imageContainerTop: offset.top,
                            imageContainerLeft: offset.left } ) } } );

                if( ( util.scrollTop >= util.maxScroll && scrollTop >= util.maxScroll ) ||
                    ( util.scrollTop === scrollTop ) || 
                    ( util.scrollTop === 0 && scrollTop <= 0 ) ) {

                    self.positionAndShowPopover();

                } else {
                    $('body,html').animate( { 'scrollTop' : scrollTop } );
                }

                return this;
            },

            getPopoverText: function() { return this.fields[ this.model.get('currentField') ].indicator.get('text'); },
            getPopoverPlacement: function() { return this.fields[ this.model.get('currentField') ].indicator.get('placement'); },

            areInputsValid: function() {
                var returnValue = true;

                _.each( this.fields, function( data, key ) {

                    if( data.validation &&
                        data.validation.get('required') === true &&
                        ! data.validation.set( 'value', this.templateData[ key ].val() ).isValid() ) {

                        inputValidator.notifyUser(
                            this.templateData[ key ],
                            { placement: data.validation.get('placement'),
                              content: data.validation.get('text') } );

                        returnValue = false;
                    }

                }, this );

                return returnValue;
            },

            nextClicked: function() {
                if( ! this.areInputsValid() ) {
                    inputValidator.scrollToFirst();
                } else {
                    this.$el.hide();
                    this.router[this.next]();
                }
            },
            
            prevClicked: function() {
                inputValidator.destroyAll();
                this.$el.hide();
                this.router[this.prev]();
            },
            

        } );
    }
);
