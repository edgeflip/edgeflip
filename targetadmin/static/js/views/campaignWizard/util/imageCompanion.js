/* Module that exports the image companion module, ued by the faces, and fb object views.
   Note that this includes its own css file.  Rather than have this view add
   classes to elements in views that inherit from it, I simply added the classes in the
   child templates.  This was probably a mistake.  These are the classes necessary
   for the image companion views :
       .companion-image ( on <img> tag )
       .input-container ( on <input> container )
       .image-container ( on <img> container )
       .popover-target ( on popover element )
    */
define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'windowUtil',
      'views/campaignWizard/util/base',
      'css!styles/campaignWizard/imageCompanion',
      'selectRange'
    ], function( $, _, Backbone, windowUtil, BaseView ) {
    
        /* Notice this inherits functionality from a base view */ 
        return BaseView.extend( {

            companionModel: new Backbone.Model(),

            /* when an input is focused or loses focus, I want to know! */
            events: {
                'focus input,textarea': 'fieldFocused',
                'blur input,textarea': 'fieldBlurred',
                'keyup [data-js=formInput]': 'fieldKeyUp'
            },

            /* listen for 'shown' event on myself to call postRender */
            initialize: function( options ) {

                _.extend( this, options ); 

                this.on('shown', this.postRender, this);
                this.on('enterPressed', this.removeAbandonedPrefill, this);
                this.on('enterPressed', this.validateInputs, this);
                this.model.on('change:name', this.updateName, this );

                this.render();

                return this;
            },

            /* adds template to DOM */
            render: function() {

                if( this.hide ) { this.$el.hide(); }

                this.slurpHtml( {
                    template: this.template(
                        _.extend( { },
                            { name: this.model.get('name') },
                            this )
                    ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                /* if we are editing a campaign, update fields */
                if( this.campaignModel ) { this.reflectCampaignState(); }
                
                return this;
            },

            /* this view has been shown to the user, initialize popup,
               gather information on the dimensions of our image when
               it has loaded, bind window resize to something so we still
               look okay */
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

            /* update input values to reflect campaign data */
            reflectCampaignState: function() {

                _.each( this.campaignModel.keys(), function( key ) {
                    this.templateData.formInput.filter('*[name="' + key + '"]').val(
                        this.campaignModel.get(key)
                    );
                }, this );
            },

            fieldKeyUp: function (event) {
                /* Handle key-up event on form inputs.
                 */
                var key = event.key, // future spec
                    keyCode = (event.keyCode || event.which),
                    target = event.currentTarget,
                    $target,
                    value,
                    currentField;

                if (key === "Tab" || keyCode === 9) {
                    $target = $(target),
                        value = $target.val(),
                        currentField = this.fields[this.companionModel.get('currentField')];

                    if (currentField.prefill && currentField.prefill === value) {
                        // Move cursor to end of prefill
                        $target.selectRange(value.length);
                    }
                }
            },
           
            /* when a field is focused update our model, scroll so that
               it is in the center of the page */ 
            fieldFocused: function(e) {
                var currentInputEl = $(e.currentTarget);
                this.companionModel.set( 'currentEl', currentInputEl );
                this.companionModel.set( 'currentField', currentInputEl.attr('name') );
                this.scrollToCurrentField();
                var currentField = this.fields[ this.companionModel.get('currentField') ];
                if( currentField.prefill && currentInputEl.val() == '' ) {
                    currentInputEl.val(currentField.prefill);
                }
                return this;
            },

            /* when a field loses focus hide the popover, update our model */
            fieldBlurred: function() {
                this.templateData.popoverEl.popover('hide');
                this.removeAbandonedPrefill();
                this.companionModel.set( 'currentField', null );
                this.companionModel.set( 'currentEl', null );
            },

            removeAbandonedPrefill: function() {
                var oldField = this.fields[ this.companionModel.get('currentField') ];
                var oldInputEl = this.companionModel.get('currentEl');
                if( oldField.prefill && oldInputEl.val() == oldField.prefill ) {
                    oldInputEl.val('');
                }
            },

            /* update our model with the dimensions of the div that is our
               image element's parent */
            setImageContainerBBox: function() {
                var offset = this.templateData.imageContainer.offset();

                this.companionModel.set( {
                    imageContainerTop: offset.top - parseFloat( this.templateData.imageContainer.css('top') ),
                    imageContainerLeft: offset.left
                } );
            },

            /* This function not only scrolls the window to our focused field,
               it also moves our image such that its vertical middle is in line with
               the focused field.
               scrollTop: the value of where we want to scroll the window
               maxDifference: the difference in height between our image, and its container,
                 the maximum we can move our image inside its container
               difference: the distance between the focused field, and the center of our image
            */
            scrollToCurrentField: function() {

                var fieldElTop = this.companionModel.get('currentEl').offset().top,
                    scrollTop = ( fieldElTop - ( windowUtil.windowHeight / 2 ) ),
                    maxDifference = this.companionModel.get('inputContainerHeight') - this.companionModel.get('imageHeight'),
                    difference = fieldElTop - ( this.companionModel.get('imageContainerTop') + ( this.companionModel.get('imageHeight') / 2 ) );

                if( difference < 0 ) { difference = 0; }
                else if( difference > maxDifference ) { difference = maxDifference; }

                this.templateData.imageContainer.animate( { 'top': difference } );
           
                /* we do not need to scroll the number under the following circumstances.
                   if we do not need to scroll the window, just show the popover */ 
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

            /* see bootstrap's docs for more info */
            showPopover: function() {

                if( this.companionModel.has('currentField') ) {
                    this.updatePopoverPosition();
                    this.templateData.popoverEl.popover('show');
                }
            },

            /* should be in base class, updates campaign name in header if it changes */
            updateName: function() {
                this.templateData.campaignName.text( this.model.get('name') );
            },

            /* put the popover over the image, or next to the field depending on
               the metadata of the field set in the inheriting view */
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

            /* if the window resizes, recalculate stuff so that our animations, popover, and
               scrolling still functions */
            windowResized: function() {

                this.setImageDimensions()
                    .setMultiplier()
                    .setBoundingBoxData();

                if( this.companionModel.has('currentField') ) {
                    this.hidePopover()
                        .showPopover();
                }
            },

            /* the coordinates set in inheriting views are for the original image size,
               so we need to handle things when the the image gets rendered to a size
               that fits on the screen */
            setMultiplier: function() {
                this.companionModel.set( {
                    multiplierX: this.companionModel.get('imageWidth') / this.companionModel.get('originalImageWidth'),
                    multiplierY: this.companionModel.get('imageHeight') / this.companionModel.get('originalImageHeight')
                } );

                return this;
            },

            /* update our model */
            setImageDimensions: function() {
                this.companionModel.set( {
                    imageWidth: this.templateData.companionImage.width(),
                    imageHeight: this.templateData.companionImage.height()
                } );

                return this;
            },

            /* the image has loaded, update our model */
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

            /* update our model */
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

            /* see bootstrap docs for more info, determines placement, content for popover */
            getPopoverText: function() { return this.fields[ this.companionModel.get('currentField') ].hoverText; },
            getPopoverPlacement: function() { return this.fields[ this.companionModel.get('currentField') ].placement; }
    } );
} );
