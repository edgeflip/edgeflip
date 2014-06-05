( function($) {
    var imageCompanion = Backbone.View.extend( {

        events: {
            'focus input,textarea': 'fieldFocused',
            'blur input,textarea': 'fieldBlurred'
        },

        initialize: function( options ) {

            $.extend( this, options );

            this.model = new Backbone.Model( {
                fieldCycleIndex: 0, 
                hasStarted: false,
                currentField: undefined,
                imageContainerTop: undefined,
                imageContainerLeft: undefined,
                inputContainerHeight: 0,
                inputContainerTop: undefined,
                inputContainerLeft: undefined,
                imageHeight: undefined,
                imageWidth: undefined,
                originalImageHeight: undefined,
                originalImageWidth: undefined,
                multiplierY: undefined,
                multiplierX: undefined
            } );

            this.slurpHtml( { slurpInputs: true } );

            this.inputEls = _.map(
                _.sortBy( _.keys( this.fields ), function( elReference ) {
                    return this.fields[ elReference ].index;
                }, this ),
                function( elReference ) { 
                    return this.templateData[ elReference ].attr( 'autocomplete', 'off' );
            }, this );

            this.util = window.util.computeSizes();

            _.each( [ 'imagePopover', 'inputPopover' ], function( popoverRef ) {
                this.templateData[ popoverRef ].popover( {
                    animation: false,
                    trigger: 'manual',
                    content: this.getPopoverText.bind( this ),
                    placement: this.getPopoverPlacement.bind( this ) 
                } );
            }, this );

            this.util.window.resize( _.debounce( this.windowResized.bind( this ), 300 ) );

            return this;
        },

        start: function() {
            if( this.templateData.image.height() ) {
                this.imageLoaded();
            } else {
                this.templateData.image.on( 'load', this.imageLoaded.bind( this ) );
            }
            
            this.model.set('hasStarted', true );
        },

        fieldFocused: function(e) {
            this.model.set( 'currentField', $(e.currentTarget).attr('name') );
            this.emboldenCurrentLabel()
                .scrollToCurrentField();
        },

        fieldBlurred: function() {
            this.weakenLabel()
                .hidePopover();
            this.model.set( 'currentField', null );
        },

        hidePopover: function() {
            this.templateData[
                this.fields[ this.model.get('currentField') ].type +
                'Popover'
            ].popover('hide');

            return this;
        },

        emboldenCurrentLabel: function() {
            this.templateData[ this.model.get('currentField') ].prev().css( 'font-weight', 'bold' );
            return this;
        },

        weakenLabel: function() {
            this.templateData[ this.model.get('currentField') ].prev().css( 'font-weight', 'normal' );
            return this;
        },

        setImageContainerBBox: function() {
            var offset = this.templateData.imageContainer.offset();

            this.model.set( {
                imageContainerTop: offset.top - parseFloat( this.templateData.imageContainer.css('top') ),
                imageContainerLeft: offset.left
            } );
        },

        scrollToCurrentField: function() {

            var fieldElTop = this.templateData[ this.model.get('currentField') ].offset().top,
                scrollTop = ( fieldElTop - ( this.util.windowHeight / 2 ) ),
                maxDifference = this.model.get('inputContainerHeight') - this.model.get('imageHeight'),
                difference = fieldElTop - ( this.model.get('imageContainerTop') + ( this.model.get('imageHeight') / 2 ) );

            if( difference < 0 ) { difference = 0; }
            else if( difference > maxDifference ) { difference = maxDifference; }

            this.templateData.imageContainer.animate( { 'top': difference } );
        
            if( ( this.util.scrollTop >= this.util.maxScroll && scrollTop >= this.util.maxScroll ) ||
                ( this.util.scrollTop === scrollTop ) || 
                ( this.util.scrollTop === 0 && scrollTop <= 0 ) ) {

                this.showPopover();

            } else {

                $('body,html').animate(
                    { 'scrollTop' : scrollTop },
                    { 'complete': this.showPopover.bind(this) }
                );
            }

            return this;
        },

        showPopover: function() {

            if( this.model.has('currentField') ) {
                this[
                    'show' +
                    this.fields[ this.model.get('currentField') ].type.capitalize() +
                    'Popover' ]();
            }

            return this;
        },

        showImagePopover: function() {

            this.templateData.inputPopover.popover('hide');

            this.updateImagePopover().popover('show');
            
            return this;
        },

        showInputPopover: function() {

            this.templateData.imagePopover.popover('hide');

            this.updateInputPopover().popover('show');
            
            return this;
        },

        updatePopoverPosition: function() {
            return this[
                'update' +
                this.fields[ this.model.get('currentField') ].type.capitalize() +
                'Popover' ]();
        },

        updateImagePopover: function() {
            var currentField = this.fields[ this.model.get('currentField') ];

            return this.templateData.imagePopover.css( {
                top: currentField.coords.y * this.model.get('multiplierY'),
                left: currentField.coords.x * this.model.get('multiplierX') } );
        },

        updateInputPopover: function() {
            var inputEl = this.templateData[ this.model.get('currentField') ],
                inputOffset = inputEl.position();

            return this.templateData.inputPopover.css( {
                top: inputOffset.top + inputEl.outerHeight( true ) + 5,
                left: inputOffset.left + ( inputEl.outerWidth( true ) / 2 ) } );
        },

        windowResized: function() {

            this.setImageDimensions()
                .setMultiplier()
                .setBoundingBoxData();

            if( this.model.has('currentField') ) {
                this.hidePopover()
                    .showPopover();
            }
        },

        setMultiplier: function() {
            this.model.set( {
                multiplierX: this.model.get('imageWidth') / this.model.get('originalImageWidth'),
                multiplierY: this.model.get('imageHeight') / this.model.get('originalImageHeight')
            } );

            return this;
        },

        setImageDimensions: function() {
            this.model.set( {
                imageWidth: this.templateData.image.width(),
                imageHeight: this.templateData.image.height()
            } );

            return this;
        },

        imageLoaded: function() {
            this.model.set( {
                originalImageHeight: this.templateData.image.height(),
                originalImageWidth: this.templateData.image.width()
            } );

            this.templateData.image.addClass( 'companion-image' );

            this.util.computeSizes();

            this.setImageDimensions()
                .setMultiplier()
                .setBoundingBoxData();

            this.beginFieldCycle();

            return this;
        },

        beginFieldCycle: function() {
            
            _.each( this.inputEls, function( $el ) {
                $el.addClass('white-text');
            } );

            this.cycleFields();

            this.inputClickedPtr = this.inputClickedDuringCycle.bind(this);
            this.keydownPtr = this.keydownDuringCycle.bind( this );

            this.$el.on( 'click', 'input,textarea', this.inputClickedPtr )
                    .on( 'keydown', 'input,textarea', this.keydownPtr );
        },


        stopCycling: function() {
            clearTimeout( this.cycleTimer );
            
            _.each( this.inputEls, function( $el ) {
                $el.removeClass('white-text');
            } );
            
            this.$el.off( 'click', 'input,textarea', this.inputClickedPtr )
                    .off( 'keydown', 'input,textarea', this.keydownPtr );

            _.each( [ 'inputClickedPtr', 'keydownPtr' ], function( attr ) { this.attr = undefined; }, this );
        },

        inputClickedDuringCycle: function( e ) {
            this.stopCycling();
        },

        keydownDuringCycle: function( e ) {
            if( e.keyCode === 27 || e.keyCode === 9 ) { this.stopCycling(); }
            if( e.keyCode === 27 ) {
                this.templateData[ this.model.get('currentField') ].blur();
            }

            return false;
        },

        cycleFields: function() {
            this.inputEls[ this.model.get('fieldCycleIndex') ].focus();
            this.model.set('fieldCycleIndex', this.model.get('fieldCycleIndex') + 1 );
            if( this.model.get('fieldCycleIndex') == this.inputEls.length ) { this.model.set('fieldCycleIndex', 0); }
            this.cycleTimer = _.delay( this.cycleFields.bind(this), 3000 );
        },

        setBoundingBoxData: function() {
            var inputContainerOffset = this.templateData.inputContainer.offset();

            this.setImageContainerBBox();

            this.model.set( {
                inputContainerTop: inputContainerOffset.top,
                inputContainerLeft: inputContainerOffset.left,
                inputContainerHeight: this.templateData.inputContainer.outerHeight( true ),
            } );

            return this;
        },

        getPopoverText: function() { return this.fields[ this.model.get('currentField') ].text; },
        getPopoverPlacement: function() { return this.fields[ this.model.get('currentField') ].placement; }


    } );

    window.imageCompanion = imageCompanion;

} )(jQuery);
