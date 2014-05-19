define(

    [ 'jquery',
      'vendor/underscore',
      'ourBackbone',
      'util',
      'filterCreator',
      'templates/filterLayer',
      'templates/filter',
      'vendor/jquery-ui',
      'css!styles/vendor/jquery-ui',
      'css!styles/campaignWizard',
    ],

    function( $, _, Backbone, util, filterCreator, filterLayerHtml, filterHtml ) {

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
                "post":     "post"
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
                faces.$el.fadeIn().removeClass('hide');
            },
            
            post: function() {
                post.$el.fadeIn().removeClass('hide');
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

        return { filterSection: filters };

        /*
        var layer_count = 1,
            can_close_modal = true;

        $('div[data-helper="img"] input').on( 'focus', function() {
            $('#' + $(this).attr('name') + '-img-helper' ).fadeIn( 400 );
        } );
        
        $('div[data-helper="img"] input').on( 'blur', function() {
            $('#' + $(this).attr('name') + '-img-helper' ).hide();
        } );

        // Tracks number of layers in play on Filtering screen

        // "Steps"
        $('.step-submit').click(function(e) {
            var step = $(this).data('step');
            if ($(this).hasClass('filter-step')) {
                var v, values, filters, layer;
                for (layer = 1; layer <= layer_count; layer++) {
                    filters = $('#enabled-filters-' + layer).sortable('toArray', 
                        {attribute: 'data-filter-id'});
                    values = [];
                    for (v = 0; v < filters.length; v++) {
                        values.push('"' + filters[v].split('=')[1] + '"');
                    }
                    $('#id_enabled-filters-' + layer).val(values);
                }
            }
            $('.wizard-step').hide();
            $('#' + step).show();
            
            if( step === 'fbobjects' ) {
                window.fbObjIndicator.init();
            }
            
            $( $('input:visible')[0] ).focus();
        } );

        // Remove Layer "X" clicked
        $('#filtering').on( 'click', '.remove-layer', function() {

            var deleted_layer_no = $(this).data('layer'),
                add_layer_btn = $('#add-layer');

            $.each( $('section[data-layer]'), function( i, layer_section ) {
                var $layer_section = $( layer_section );
                if( $layer_section.data('layer') == deleted_layer_no ) {

                    $.each( $layer_section.find('div[data-filter-id]'), function( j, layer_filter ) {
                        var $layer_filter = $(layer_filter),
                            layer_filter_id = $layer_filter.data('filter-id');
                            
                        if( ( $('#existing-filters').find( 'div[data-filter-id="' + layer_filter_id + '"]' ).length === 0 ) &&
                            ( $('#enabled-filters-1').find( 'div[data-filter-id="' + layer_filter_id + '"]' ).length === 0 ) ) {

                            $('#existing-filters').append( $layer_filter );
                        }
                        
                    } );

                    $layer_section.fadeOut( 400, function() {
                        $(this).empty().remove();

                        $.each( $('*[data-layer]'), function( k, el ) {
                            var $el = $(el),
                                el_layer_no = $el.data('layer'),
                                new_layer_no = el_layer_no - 1;

                            if( el_layer_no > deleted_layer_no ) {
                                
                                $el.data( 'layer', new_layer_no );

                                if( $el.prop('tagName') === 'SECTION' ) {

                                    $el.find('h5').first().text( 'Layer ' + new_layer_no );

                                    $('#id_enabled-filters-' + el_layer_no )
                                        .attr( { "id": 'id_enabled-filters-' + new_layer_no,
                                                 "name": 'enabled-filters-' + new_layer_no } );
                                               
                                    $('#enabled-filters-' + el_layer_no )
                                        .attr( { "id": 'enabled-filters-' + new_layer_no } );
                                }
                            }
                        } );
                    } );
                }
            } );

            layer_count--;
            add_layer_btn.data( 'layer-count', layer_count );

            if( add_layer_btn.prop( 'disabled' ) ) {
                add_layer_btn.prop( 'disabled', false );
            }
            
        } );

        // Sortables - Drag and Drop stuff
        $(function() {
            $('#existing-filters').sortable({
                connectWith: ".target-well"
            });
            $('#enabled-filters-1').sortable({
                connectWith: ".target-well"
            });
            $( ".sortable" ).disableSelection();
        });

        // Layer addition
        $('#add-layer').click(function(event){
            event.preventDefault();
            var previous_layer_html = $('#enabled-filters-' + layer_count).html()
            var hidden_elements = $('.hidden-elements')
            layer_count = $('#add-layer').data('layer-count') + 1;
            $('#add-layer').data('layer-count', layer_count);
            $('#enabled-section').append(
                '<section data-layer="' + layer_count + '">' +
                '<div class="clearfix"><h5 class="layer-text-header pull-left">Layer ' + layer_count + '</h5>' +
                '<h5 data-layer="' + layer_count + '" class="btn btn-link pull-right remove-layer">' +
                '<i class="icon-remove"></i></h5></div><div class="clearfix"><input type="hidden" id="id_enabled-filters-' + 
                layer_count + '" name="enabled-filters-' + layer_count + 
                '"><div style="margin-left: 0px; min-height:54px;" class="span12 well sortable target-well" id="enabled-filters-' + 
                layer_count + '">' + previous_layer_html  + '</div></div></section>'
            );

            $('#enabled-filters-' + layer_count).sortable({
                connectWith: '.target-well'
            });
            // Aribtrary limit, but seems about right. Subject to change
            if (layer_count >= 4) {
                $('#add-layer').prop('disabled', true);
            }
        });

        // New FilterFeature creation
        $('#filter-add').click(function(event) {
            event.preventDefault()
            var filter_values = '';
            $('.filter-val-input').each(function(index){
                var value = $(this).val();
                if (value) {
                    if (filter_values === ''){
                        filter_values = value;
                    } else {
                        filter_values += '||' + value;
                    }
                }
            });
            if (filter_values.slice(-2) === '||'){
                filter_values = filter_values.substr(0, filter_values.length - 2);
            }
            $('#id_value').val(filter_values);
            var validation_elems = [
                [$('#id_feature'), $('#feature-error')],
                [$('#id_operator'), $('#operator-error')],
                [$('#id_value'), $('#value-error')]
            ]
            var form_errors = false;
            for (var elem=0; elem < validation_elems.length; elem++) {
                if (validation_elems[elem][0].val() === ""){
                    validation_elems[elem][1].show();
                    form_errors = true;
                } else {
                    validation_elems[elem][1].hide();
                }
            }
            if (!form_errors) {
                var feature = $('#id_feature').val();
                var operator = $('#id_operator').val();
                var filter_values = $('#id_value').val();
                $('#existing-filters').prepend(
                    '<div data-filter-id="set_number=' + feature + '.' + operator + 
                    '.' + filter_values + '" class="span2 draggable"><p><abbr title="' + 
                    feature + ' ' + operator + ' ' + filter_values + '">' + 
                    feature + ' ' + ' ' + operator + ' ' + filter_values.slice(0, 15) + 
                    '</abbr></p></div>'
                );

                if( can_close_modal ) {
                    $('#filter-modal').modal('toggle');
                    $('#filter-modal').removeData();
                }
            }
        });
        
        $( $('input:visible')[0] ).focus();
        */
    }
);
