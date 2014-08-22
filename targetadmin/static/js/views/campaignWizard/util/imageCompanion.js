define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'windowUtil',
      'views/campaignWizard/util/base',
      'css!styles/campaignWizard/imageCompanion'
    ], function( $, _, Backbone, windowUtil, BaseView ) {
     
        return BaseView.extend( {

            companionModel: new Backbone.Model(),

            events: {
                'focus input,textarea': 'fieldFocused',
                'blur input,textarea': 'fieldBlurred'
            },

            initialize: function( options ) {

                _.extend( this, options ); 

                this.on('shown', this.postRender, this);

                this.render();

                return this;
            },

            render: function() {

                if( this.hide ) { this.$el.hide(); }

                this.slurpHtml( {
                    template: this.template(
                        _.extend( { },
                            { name: this.model.get('name') },
                            this )
                    ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                if( this.campaignModel ) { this.reflectCampaignState(); }
                
                return this;
            },

            postRender: function() {

                this.templateData.popoverEl.popover( {
                    animation: false,
                    trigger: 'manual',
                    content: this.getPopoverText.bind( this ),
                    placement: this.getPopoverPlacement.bind( this )
                } );

                if( this.templateData.companionImage.height() ) {
                    this.imageLoaded();
                } else {
                    this.templateData.companionImage.on( 'load', this.imageLoaded.bind( this ) );
                }

                windowUtil.window.resize( _.debounce( this.windowResized.bind( this ), 300 ) );
                
                return this; 
            },

            reflectCampaignState: function() {

                _.each( this.campaignModel.keys(), function( key ) {
                    this.templateData.formInput.filter('*[name="' + key + '"]').val(
                        this.campaignModel.get(key)
                    );
                }, this );
            },
            
            fieldFocused: function(e) {
                var currentInputEl = $(e.currentTarget);
                this.companionModel.set( 'currentEl', currentInputEl );
                this.companionModel.set( 'currentField', currentInputEl.attr('name') );
                this.scrollToCurrentField();

                return this;
            },

            fieldBlurred: function() {
                this.templateData.popoverEl.popover('hide');
                this.companionModel.set( 'currentField', null );
                this.companionModel.set( 'currentEl', null );
            },

            setImageContainerBBox: function() {
                var offset = this.templateData.imageContainer.offset();

                this.companionModel.set( {
                    imageContainerTop: offset.top - parseFloat( this.templateData.imageContainer.css('top') ),
                    imageContainerLeft: offset.left
                } );
            },

            scrollToCurrentField: function() {

                var fieldElTop = this.companionModel.get('currentEl').offset().top,
                    scrollTop = ( fieldElTop - ( windowUtil.windowHeight / 2 ) ),
                    maxDifference = this.companionModel.get('inputContainerHeight') - this.companionModel.get('imageHeight'),
                    difference = fieldElTop - ( this.companionModel.get('imageContainerTop') + ( this.companionModel.get('imageHeight') / 2 ) );

                if( difference < 0 ) { difference = 0; }
                else if( difference > maxDifference ) { difference = maxDifference; }

                this.templateData.imageContainer.animate( { 'top': difference } );
            
                if( ( windowUtil.scrollTop >= windowUtil.maxScroll && scrollTop >= windowUtil.maxScroll ) ||
                    ( windowUtil.scrollTop === scrollTop ) || 
                    ( windowUtil.scrollTop === 0 && scrollTop <= 0 ) ) {

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

                if( this.companionModel.has('currentField') ) {
                    this.updatePopoverPosition();
                    this.templateData.popoverEl.popover('show');
                }
            },

            updatePopoverPosition: function() {
                var currentField = this.fields[ this.companionModel.get('currentField') ],
                    currentEl = this.companionModel.get('currentEl');

                if( currentField.imageCoords ) {
                    this.templateData.popoverEl.appendTo( this.templateData.imageContainer );
                    
                    this.templateData.popoverEl.css( {
                        top: currentField.imageCoords.y * this.companionModel.get('multiplierY'),
                        left: currentField.imageCoords.x * this.companionModel.get('multiplierX')
                    } ); 

                } else {
                    
                    this.templateData.popoverEl.appendTo( this.templateData.inputContainer );
                    
                    this.templateData.popoverEl.css( {
                        top: currentEl.position().top + ( currentEl.outerHeight() ) + 5,
                        left: currentEl.position().left + ( currentEl.outerWidth() / 2 )
                    } );
                }
            },

            windowResized: function() {

                this.setImageDimensions()
                    .setMultiplier()
                    .setBoundingBoxData();

                if( this.companionModel.has('currentField') ) {
                    this.hidePopover()
                        .showPopover();
                }
            },

            setMultiplier: function() {
                this.companionModel.set( {
                    multiplierX: this.companionModel.get('imageWidth') / this.companionModel.get('originalImageWidth'),
                    multiplierY: this.companionModel.get('imageHeight') / this.companionModel.get('originalImageHeight')
                } );

                return this;
            },

            setImageDimensions: function() {
                this.companionModel.set( {
                    imageWidth: this.templateData.companionImage.width(),
                    imageHeight: this.templateData.companionImage.height()
                } );

                return this;
            },

            imageLoaded: function() {
                this.companionModel.set( {
                    originalImageHeight: this.templateData.companionImage.height(),
                    originalImageWidth: this.templateData.companionImage.width()
                } );

                this.templateData.companionImage.addClass( 'companion-image' );

                windowUtil.computeSizes();

                this.setImageDimensions()
                    .setMultiplier()
                    .setBoundingBoxData();

                return this;
            },

        setBoundingBoxData: function() {
            var inputContainerOffset = this.templateData.inputContainer.offset();

            this.setImageContainerBBox();

            this.companionModel.set( {
                inputContainerTop: inputContainerOffset.top,
                inputContainerLeft: inputContainerOffset.left,
                inputContainerHeight: this.templateData.inputContainer.outerHeight( true ),
            } );

            return this;
        },

        getPopoverText: function() { return this.fields[ this.companionModel.get('currentField') ].hoverText; },
        getPopoverPlacement: function() { return this.fields[ this.companionModel.get('currentField') ].placement; }
    } );
} );
