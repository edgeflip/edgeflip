$( function() {    

    window.campaignWizard = new ( Backbone.View.extend( {

        initialize: function() {

            $('i.icon-question-sign').popover( { trigger: 'hover' } );
        }

    } ) )( { el: '#wizard-form' } );

    var layer_count = 1,
        myWindow = $(window);

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
                    if( filters[v] ) {
                        values.push('"' + filters[v].split('=')[1] + '"');
                    }
                }
                $('#id_enabled-filters-' + layer).val(values);
            }
        }
        $('.wizard-step').hide();
        $('#' + step).show();
        
        if( step === 'faces' && (! window.facesImageCompanion.model.get('hasRendered') ) ) {
            window.facesImageCompanion.afterRender();
        }
        
        if( step === 'fbobjects' && (! window.fbObjImageCompanion.model.get('hasRendered') ) ) {
            window.fbObjImageCompanion.afterRender();
        }

        if( step === 'intro' ) {
            $('#intro-header').fadeIn();    
            $('.campaign-name').addClass('hide');
        } else {
            $('#intro-header').fadeOut();    
            $('.campaign-name').removeClass('hide');
        }

        if( $(this).attr('id') === 'step1-next' ) {
            $('.campaign-name span').text( $('#id_name').val() );
        }
       
        $('body,html').scrollTop( 0 );
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

    filterReceived = function( event, ui ) {
        var dataLink = ui.item.attr('data-link');
        if( dataLink ) {
            ui.sender.find('[data-link="' + dataLink + '"]').appendTo( $(event.target) );
        }
    }
    
    // Sortables - Drag and Drop stuff
    $(function() {
        $('#existing-filters').sortable({
            connectWith: ".target-well",
            receive: filterReceived
        });
        $('#enabled-filters-1').sortable({
            connectWith: ".target-well",
            receive: filterReceived
        });
        $( ".sortable" ).disableSelection();
    });

    $('#filtering').on( 'dblclick', '.draggable', function() {
        var clickedEl = $(this),
            dataLink = clickedEl.attr('data-link'),
            lastEnabled = $('#enabled-section').find('.target-well').last(),
            availableFilters = $('#existing-filters');

        if( clickedEl.parent().attr('id') === 'existing-filters' ) {
            if( dataLink ) {
                clickedEl.siblings('[data-link="' + dataLink + '"]').appendTo( lastEnabled );
            }
            lastEnabled.append( clickedEl );
        } else {
            if( dataLink ) {
                clickedEl.siblings('[data-link="' + dataLink + '"]').appendTo( availableFilters );
            }
            clickedEl.appendTo( availableFilters );
        }
    } );


    // Layer addition
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

    $('#step2-prev').on( 'click', function() {
        carouselEl.carousel('cycle');
    } );

} );
