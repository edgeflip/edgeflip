( function($) {
    window.campaignWizardFilterView = Backbone.View.extend( {

        emptyFallbackHelpText: "We recommend selecting the 'empty fallback' feature in case some of your supporters have few friends in your Target and Fallback Audiences. When the empty fallback feature is selected, the Targeted Sharing application will still suggest the friends most likely to support your organization, even though no filters are enabled. The 'empty fallback' feature is selected by default for new campaigns.",

        events: {
            'click [data-js="learnMoreBtn"]': 'learnMoreClicked',
            'click [data-js="addLayerBtn"]': 'addLayerClicked'
        },

        initialize: function( options ) {

            _.extend( this, options );

            this.model = new Backbone.Model( {
                layerCount: 1
            } );

            this.slurpHtml();

            this.insertExistingFilters();

            this.templateData.emptyFallbackHelpText.append( this.emptyFallbackHelpText );
            this.templateData.emptyFallbackHelpIcon.data( 'content', this.emptyFallbackHelpText );
        },

        learnMoreClicked: function() {
            $('#target-audience-help-modal').modal();
        },

        filterTemplate: function( data ) {
            return '<div title="' + data.readable + '" data-filter-id="set_number=' + [ data.feature, data.operator, data.value ].join('.') + '" class="span2 draggable">' +
                '<div class="filter-content-container"><span class="filter">' + data.readable + '</span></div></div>';
        },

        layerTemplate: function( data ) {
            return '<section class="span12" data-layer="' + data.layerCount + '">' +
            '<div class="row"><div class="span11"><h6 class="layer-text-header pull-left"><span>Fallback Audience ' + (data.layerCount - 1) + '</span></h6></div>' +
            '<div class="span1"><h6 data-layer="' + data.layerCount + '" class="btn btn-link pull-right remove-layer">' +
            '<i class="icon-remove"></i></h6></div></div><input type="hidden" id="id_enabled-filters-' + 
            data.layerCount + '" name="enabled-filters-' + data.layerCount + 
            '"><div data-js="enabledFilters" class="clearfix well sortable target-well filter-well" id="enabled-filters-' + 
            data.layerCount + '">' + data.previousLayerHtml  + '</div></section>';
        },

        insertExistingFilters: function() {
            this.filters.each( function( filter ) {
                this.templateData.existingFilters.append(
                    this.filterTemplate(
                        _.extend( filter.attributes, { readable: filter.getReadable() } ) ) );
            }, this );
        },

        addLayerClicked: function() {
            this.model.set( 'layerCount', this.model.get('layerCount') + 1 );

            this.slurpHtml( {
                template: this.layerTemplate( {
                    layerCount: this.model.get('layerCount'),
                    previousLayerHtml: this.templateData.enabledFilters.last().html()
                } ),
                insertion: { $el: this.templateData.enabledFiltersContainer, method: 'append' }
            } );

            this.templateData.enabledFiltersContainer.children('section').last().find('h6').first().append( this.templateData.addLayerBtn );

            this.templateData.enabledFilters.last().sortable( { connectWith: ".target-well" } );
            
            if( this.model.get( 'layerCount' ) === 4 ) {
                this.templateData.addLayerBtn.prop( 'disabled', true );
            }
        }

    } );

} )(jQuery);

/*
$('#add-layer').click(function(event){
        event.preventDefault();
        var previous_layer_html = $('#enabled-filters-' + layer_count).html()
        var hidden_elements = $('.hidden-elements')
        layer_count = $('#add-layer').data('layer-count') + 1;
        $('#add-layer').data('layer-count', layer_count);
        $('#enabled-section').append(
            '<section class="span12" data-layer="' + layer_count + '">' +
            '<div class="row"><div class="span11"><h6 class="layer-text-header pull-left"><span>Fallback Audience ' + (layer_count - 1) + '</span></h6></div>' +
            '<div class="span1"><h6 data-layer="' + layer_count + '" class="btn btn-link pull-right remove-layer">' +
            '<i class="icon-remove"></i></h6></div></div><input type="hidden" id="id_enabled-filters-' + 
            layer_count + '" name="enabled-filters-' + layer_count + 
            '"><div class="clearfix well sortable target-well filter-well" id="enabled-filters-' + 
            layer_count + '">' + previous_layer_html  + '</div></section>'
        );

        $('#enabled-section').children('section').last().find('h6').first().append( $('#add-layer') );

        $('#enabled-filters-' + layer_count).sortable({
            connectWith: '.target-well',
            receive: filterReceived
        });
        // Aribtrary limit, but seems about right. Subject to change
        if (layer_count >= 4) {
            $('#add-layer').prop('disabled', true);
        }
    });


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
                    var found = false;
     
                    if( $(this).find('#add-layer').length ) { 
                        $('#add-layer').hide().appendTo($('body'));
                        found = true;
                    }

                    $(this).empty().remove();

                    if( found ) {
                        if( $('#enabled-section').children('section').length ) {
                            $('#enabled-section').children('section').last().find('h6').first().append( $('#add-layer').show() );
                        } else {
                            $('#enabled-section').children('h6').first().append( $('#add-layer').show() );
                        }
                    }

                    $.each( $('*[data-layer]'), function( k, el ) {
                        var $el = $(el),
                            el_layer_no = $el.data('layer'),
                            new_layer_no = el_layer_no - 1;

                        if( el_layer_no > deleted_layer_no ) {
                            
                            $el.data( 'layer', new_layer_no );

                            if( $el.prop('tagName') === 'SECTION' ) {

                                $el.find('h6 span').first().text( 'Fallback Audience ' + ( new_layer_no - 1 ) );

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
*/
