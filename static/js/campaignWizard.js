define(

    [ 'jquery',
      'vendor/underscore',
      'ourBackbone',
      'util',
      'filterCreator',
      'indicator',
      'inputValidator',
      'templates/filterLayer',
      'templates/filter',
      'vendor/jquery-ui',
      'css!styles/vendor/jquery-ui',
      'css!styles/campaignWizard',
    ],

    function( $, _, Backbone, util, filterCreator, indicator, filterLayerHtml, filterHtml ) {

        var router = new ( Backbone.Router.extend( {

            initialize: function() {
                $( function() {
                    Backbone.history.start( { root: "/admin/client/1/campaign/wizard/" } )
                } );
            },

            routes: {
                "":         "intro",
                "intro":    "intro",
                "audience": "filters",
                "faces":    "faces",
                "fb-post":  "fbObj"
            },

            intro: function() {
                intro.$el
                    .fadeIn( 400, function() { intro.setCarouselHeight.call( intro ) } )
                    .removeClass('hide');
            },
            
            filters: function() {
                filters.$el.fadeIn().removeClass('hide');
            },
            
            faces: function() {
                faces.$el.fadeIn( 400, function() { faces.shown(); } )
                         .removeClass('hide');
            },
           
            fbObj: function() {
                fbObj.$el.fadeIn( 400, function() { fbObj.shown(); } )
                          .removeClass('hide');
            }

        } ) )();

        var wizardView = Backbone.View.extend( {

            initialize: function() {
                this.slurpHtml( { slurpInputs: true } );
            }
        } );

        var intro = new ( wizardView.extend( { 

            config: {
                carousel: {
                    interval: 20000,
                    bottomPadding: 20,
                }
            },

            initialize: function() {
                var self = this;

                wizardView.prototype.initialize.call(this); 

                util.window.on( 'resize', _.debounce( function() { self.setCarouselHeight() }, 200 ) );

                this.templateData.carouselEl.carousel( {
                    interval: this.config.carousel.interval,
                    pause: "" } );
               
                this.templateData.nameModal.on( 'hide.bs.modal',
                    function() { self.modalHidden(); } );
            },

            events: {
                'click img[data-js="carouselImage"]': 'carouselImageClick',
                'click button[data-js="nameSubmitBtn"]': 'nameSubmitted',
            },

            setCarouselHeight: function( opts ) {

                this.templateData.carouselEl.animate( {
                    'height': util.windowHeight -
                        this.templateData.carouselEl.offset().top -
                        this.config.carousel.bottomPadding } );
            },

            carouselImageClick: function() {
                this.templateData.carouselEl.carousel('pause');
                this.templateData.nameModal.modal();
                this.bindKeyDown();
            },

            modalHidden: function() {
                this.templateData.carouselEl.carousel('cycle');
                this.unbindKeyDown();
            },

            nameSubmitted: function() {
                if( $.trim( this.templateData.name.val() ) !== '' ) {
                    this.unbindKeyDown();
                    this.templateData.nameModal.modal('hide');
                    this.$el.hide();
                    router.navigate( 'audience', { trigger: true } );
                }
            },

            bindKeyDown: function() {
                var self = this;

                this.handleKeyDown = function(e) {
                    if( e.keyCode === 13 ) {
                        self.nameSubmitted();
                    }
                };

                util.document.on( 'keydown', this.handleKeyDown );
            },

            unbindKeyDown: function() {
                util.document.off( 'keydown', this.handleKeyDown );
            }


        } ) )( { el: '#intro' } );

        var filters = new ( wizardView.extend( { 

            events: {
                'click button[data-js="addLayerBtn"]': 'addLayerClicked',
                'click button[data-js="addFilterBtn"]': 'addFilterClicked',
                'click button[data-js="nextBtn"]': 'nextClicked',
                'click button[data-js="previousBtn"]': 'previousClicked',
                'click h5[data-js="removeLayerBtn"]': 'removeLayerClicked',
            },

            initialize: function() {
                wizardView.prototype.initialize.call(this); 

                this.model = new Backbone.Model( {
                    layerCount: 1 } );

                $( this.initDragDrop.bind(this) );

                this.templateData.helpText.popover( { trigger: 'hover' } );
            },

            initDragDrop: function() {

                _.each( [ 'availableFilters', 'enabledFilters' ], function( elRef ) {
                    this.templateData[ elRef ]
                        .sortable( { connectWith: ".target-well" } )
                        .disableSelection()
                }, this );
            },

            setAvailableFilters: function( filters ) {

                filters.each( function( filter ) {
                    filter.set( 'shortValue', filter.get('value').slice(0, 15) );
                    this.templateData.availableFilters.append( filterHtml( filter.attributes ) );
                }, this );
            },
            
            addFilterClicked: function() {
                var self = this;

                this.templateData.addFilterModal.on( 'shown.bs.modal', function() {
                    if( self.filterCreator === undefined ) {
                       self.filterCreator = new filterCreator( { el: '#filter-modal' } );
                    }
                } );
            },

            addLayerClicked: function() {

                this.model.set( 'layerCount', this.model.get('layerCount') + 1 );

                this.slurpHtml( {
                    template: filterLayerHtml( {
                        layerNumber: this.model.get('layerCount'),
                        content: this.templateData.enabledFilters.last().html()
                    } ),
                    insertion: { $el: this.templateData.enabledFiltersContainer, method: 'append' } } );

                this.templateData.enabledFilters.last().sortable( { connectWith: ".target-well" } );
            
                // Aribtrary limit, but seems about right. Subject to change
                if( this.model.get( 'layerCount' ) >= 4 ) {
                    this.templateData.addLayerBtn.prop( 'disabled', true );
                }
            },

            removeLayerClicked: function( e ) {
                var self = this;

                this.model.set( 'layerCount', this.model.get('layerCount') - 1 );

                $( e.target ).closest('[data-js="layerContainer"]')
                    .fadeOut( 400, function() {
                        $(this).empty().remove();
                        self.updateLayerNumbers(); } );

                if( this.templateData.addLayerBtn.prop( 'disabled' ) ) {
                    this.templateData.addLayerBtn.prop( 'disabled', false );
                }
            },

            updateLayerNumbers: function() {

                this.templateData.layerHeading.each( function( i, el ) {
                    $(el).text( 'Layer ' + ( i + 1 ) ) } );
                
                this.templateData.layerInput.each( function( i, el ) {
                    $(el).attr( 'name', 'id_enabled-filters-' + ( i + 1 ) ) } );
            },

            nextClicked: function() {
                this.$el.hide(); 
                router.navigate( 'faces', { trigger: true } );
            },

            previousClicked: function() {
                this.$el.hide(); 
                router.navigate( 'intro', { trigger: true } );
            }

        } ) )( { el: '#filters' } );

        var faces = new indicator( {
            el: '#faces',
            next: 'fb-post',
            prev: 'audience',
            router: router,
            fields: {
                sharing_prompt: {
                    coords: { x: 380, y: 134 },
                    placement: 'bottom',
                    text: "Your headline will go here."
                },

                sharing_sub_header: {
                    coords: { x: 384, y: 189 },
                    placement: 'bottom',
                    text: "Your sub header will go here."
                },

                thanks_url: {
                    coords: { x: 524, y: 813 },
                    placement: 'left',
                    text: "Where should we send your supporters after they share with their friends?"
                },
                
                error_url: {
                    text: [ "If the user does not have any friends that fit the targeting criteria ",
                            "or if there is a sharing error, they will be sent to this URL " ].join("")
                },
                
                faces_url: {
                    text: [ "Provide the URL where this page will be embedded. ",
                            "Leave blank if using Facebook canvas." ].join("")
                }
            }
        } );

        var fbObj = new indicator( {
            el: '#fb-obj',
            prev: 'faces',
            router: router,
            fields: {
                org_name: {
                    coords: { x: 540, y: 80 },
                    placement: 'bottom',
                    text: "The cause or organization you enter will replace 'Freakonomics Radio' here."
                },

                msg1_pre: {
                    coords: { x: 56, y: 206 },
                    placement: 'bottom',
                    text: "Text to be displayed before friend names."
                },
                
                msg1_post: {
                    coords: { x: 519, y: 204 },
                    placement: 'bottom',
                    text: "Text that will go after the friend names."
                },

                msg2_pre: {
                    coords: { x: 56, y: 206 },
                    placement: 'bottom',
                    text: "Alternate text to suggest before friend names so that your supporters's feeds don't all look the same."
                },
                
                msg2_post: {
                    coords: { x: 519, y: 204 },
                    placement: 'bottom',
                    text: "Alternate text for after the friend names.  We will randomly pick a suggestion."
                },

                og_title: {
                    coords: { x: 386, y: 754 },
                    placement: 'bottom',
                    text: "Your title will go here."
                },
                
                og_image: {
                    coords: { x: 641, y: 417 },
                    placement: 'right',
                    text: "Your image will go here."
                },
                
                og_description: {
                    coords: { x: 464, y: 861 },
                    placement: 'bottom',
                    text: "Your description will go here."
                },

                content_url: {
                    el: $('input[name="content_url"]'),
                    text: "When someone clicks on the post, this is where we will send them."
                }
            }

        } );

        return { filterSection: filters };
    }
);
