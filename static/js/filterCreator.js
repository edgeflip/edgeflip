define(
    [
      'jquery',
      'vendor/underscore',
      'ourBackbone',
      'templates/proposedLocation',
      'templates/filter',
      'usStates',
      'vendor/bootstrap3-typeahead',
      'vendor/jquery-ui',
      'css!styles/vendor/jquery-ui',
      'css!styles/filterCreator'
    ],
    
    function( $, _, Backbone, proposedLocationHtml, filterHtml, usStates ) {

        var filterCreator = Backbone.View.extend( {

            model: new Backbone.Model( {
                state: 'default',
                locationState: undefined
            } ),

            events: {
                'change select[data-js="locationTypeDropdown"]': 'locationTypeChanged',
                'change select[name="feature"]': 'featureChanged',
                'change select[data-js="genderDropdown"]': 'genderChanged',
                'click button[data-js="addLocationBtn"]': 'addLocationClicked',
                'click div[data-js="removeProposedLocationBtn"]': 'removeProposedLocation',
                'click button[data-js="saveFilterBtn"]': 'saveFilterClicked'
            },

            initialize: function() {
                var self = this;

                this.slurpHtml( { slurpInputs: true } );
                
                this.templateData.locationTypeDropdown.popover( { trigger: 'manual' } );
                this.templateData.addLocationBtn.popover( { trigger: 'manual' } );

                this.templateData.ageRange.slider( {
                    range: true,
                    min: 0,
                    max: 100,
                    values: [ 25, 75 ],
                    slide: function( event, ui ) {
                        self.updateAgeRangeDisplay( ui.values[0], ui.values[1] ); }
                } );

                this.templateData.stateInput.typeahead( {
                     source: usStates.values,
                     items: 3
                } );

                $('#filter-modal').on('hide.bs.modal', function() { self.cleanUp() } );
            },

            updateAgeRangeDisplay: function( min, max ) {
                this.templateData.ageRangeDisplay.text( min + " - " + max );
            },

            locationTypeChanged: function() {

                var locationType = this.templateData.locationTypeDropdown.val(),
                    capitalizedLocationType = locationType.charAt(0).toUpperCase() + locationType.slice(1);

                if( this.model.get('locationState') !== undefined ) {
                    this.templateData[ this.model.get('locationState') + 'Container' ].hide();
                }

                this.templateData[ locationType + 'Container' ].fadeIn();

                if( locationType ) {
                    this.templateData.addLocationBtn
                        .text( 'Add ' + capitalizedLocationType )
                        .fadeIn().removeClass('hide');
                } else {
                    this.templateData.addLocationBtn.hide();
                }

                this.model.set( 'locationState', locationType );

                this.templateData.proposedLocationsContainer.hide();
                this.templateData.proposedLocations.empty();

                return this;
            },

            featureChanged: function() {
                var feature = this.templateData.feature.val();

                this.cleanupUI[ ( this.cleanupUI[ this.model.get('state') ] ) ? this.model.get('state') : 'default' ].call( this );
                this.showUI[ ( this.showUI[ feature ] ) ? feature : 'default' ].call( this );

                this.model.set( 'state', feature );

                return this;
            },

            genderChanged: function() {
                this.templateData.firstValueInput.val( this.templateData.genderDropdown.val() );
                return this;
            },

            addLocationClicked: function( e ) {

                var input = this.templateData[ this.model.get('locationState') + 'Input' ],
                    val = $.trim( input.val() ),
                    self = this;

                var text = ( input.prop('tagName') === 'SELECT' )
                    ? $( input.find('option[value="' + val + '"]') ).text()
                    : val;

                if( val === '' ) { return; }

                this.templateData.proposedLocationsContainer.fadeIn();

                if( ( this.templateData.stateContainer.is(':visible') ) &&
                    ( ! _.contains( usStates.values, val ) ) ) {

                    e.stopPropagation();

                    this.templateData.addLocationBtn.attr( 'data-content', 'Invalid State' ).popover('show');
                    this.delegateRemovePopover( this.templateData.addLocationBtn );
                    return;
                }

                if( this.templateData.proposedLocations.children().length ) {

                    if( this.templateData.proposedLocations.find( 'div[data-val="' + val + '"]' ).length ) {

                        e.stopPropagation();

                        this.templateData.addLocationBtn.attr( 'data-content', 'This filter has already been added' ).popover('show');
                        this.delegateRemovePopover( this.templateData.addLocationBtn );
                        return;
                    }
                }

                this.templateData.proposedLocations.append(
                    proposedLocationHtml( {
                        notFirst: ( this.templateData.proposedLocations.children().length > 0 ),
                        val: val,
                        text: text } ) );

                input.val('');
            },

            removeProposedLocation: function( e ) {
                var row = $( $( e.currentTarget ).parent() ),
                    prevEl = row.prev('.filter-or'),
                    nextEl = row.next('.filter-or');

                if( prevEl.length ) { prevEl.fadeOut( 400, function() { prevEl.remove(); } ); }
                else if( nextEl.length ) { nextEl.fadeOut( 400, function() { nextEl.remove(); } ); }

                row.fadeOut( 400, function() { row.empty().remove() } );
            },

            saveFilterClicked: function() {
                return this.filterHandlers[ ( this.filterHandlers[ this.model.get('state') ] )
                    ? this.model.get('state')
                    : 'generic' ].call( this );
            },

            cleanUp: function() {

                //if( e && $(e.target).attr('data-content') ) { return; }
                this.templateData.feature.val('');

                this.cleanupUI[ ( this.cleanupUI[ this.model.get('state') ] )
                    ? this.model.get('state') : 'default' ].call( this );

                this.model.set( 'state', 'default' );
            },

            filterHandlers: {

                location: function() {
                    var self = this,
                        filters = this.templateData.proposedLocations.children();

                    if( ! this.templateData.locationTypeDropdown.val() ) {
                        this.templateData.locationTypeDropdown.popover('show');
                        this.delegateRemovePopover( this.templateData.locationTypeDropdown );
                        return;
                    }

                    if( filters.length === 0 ) {
                        this.templateData.addLocationBtn.attr( 'data-content', 'Please add a filter.' ).popover('show');
                        this.delegateRemovePopover( this.templateData.addLocationBtn );
                        return;
                    }

                    filters.each( function( i, filterEl ) {
                        var new_id = 'id_value-split-' + parseInt( i + 1 );
                        if( i === 0 ) { self.templateData.firstValueInput.val( $(filterEl).data('val') ); }
                        else {
                            self.templateData.extraValues.append(    
                                $('<input id="' + new_id + '" name="' + new_id + '" type="text" class="filter-val-input">').val( $(filterEl).data('val') )
                            );
                        }
                    } );

                    this.setFilterValue();
                    this.templateData.operator.val('in');
                    this.createFilter( { feature: this.model.get('locationState') } );

                    return this.close();
                },

                //creates two filters, min age, max age based on slider values
                age: function() {

                    var values = this.templateData.ageRange.slider( 'values' );

                    this.templateData.operator.val('min');
                    this.templateData.value.val( values[0] );
                    this.createFilter();
                    
                    this.templateData.operator.val('max');
                    this.templateData.value.val( values[1] );
                    this.createFilter();

                    return this.close();
                },

                //generic add filter
                //  setFilterValue handles 1 or many text inputs
                //  isValid makes sure we have stuff
                //  createFilter does what it says ( only on the client though )
                //  this is something that needs to be addressed
                generic: function() {

                    this.setFilterValue();

                    if( this.isValid() ) { this.createFilter().close(); }
                    
                    return this;
                }
            },

            isValid: function() {

                var validation_elems = [
                    [ 'feature' ],
                    [ 'operator' ],
                    [ 'value'  ] ],

                    isValid = true;

                for(var elem=0; elem < validation_elems.length; elem++) {
                    if( this.templateData[ validation_elems[elem][0] ].val() === "" ) {
                        isValid = false;
                        break;
                    }
                }

                return isValid;
            },

            //this function was lifted from legacy code
            //  it takes one or more filter values and ors (||) them 
            setFilterValue: function() {
                var filter_values = '';

                $('.filter-val-input').each( function( index ) {
                    var value = $(this).val();
                    if( value ) {
                        if( filter_values === '' ) {
                            filter_values = value;
                        } else {
                            filter_values += '||' + value;
                        }
                    }
                } );

                if( filter_values.slice(-2) === '||' ) {
                    filter_values = filter_values.substr(0, filter_values.length - 2);
                }

                this.templateData.value.val( filter_values );

                return this;
            },

            //this function was lifted from legacy code
            createFilter: function( opts ) {
                var feature = ( opts && opts.feature ) ? opts.feature : this.templateData.feature.val(),
                    operator = this.templateData.operator.val(),
                    filter_values = this.templateData.value.val();

                $('#existing-filters').prepend( filterHtml( {
                        feature: feature,
                        operator: operator,
                        value: filter_values,
                        shortValue: filter_values.slice(0, 15) } ) );

                return this;
            },

            delegateRemovePopover: function( popoverEl ) {
                var self = this;

                if( ! this.removePopoverHandler ) {
                    this.removePopoverHandler = function() { self.removePopup(); };
                }

                this.currentPopover = popoverEl;
                $(document).on( 'click', this.removePopoverHandler );
            },

            removePopup: function() {
                this.currentPopover.popover('hide');
                $(document).off( 'click', this.removePopoverHandler );
            },
           
            showUI: {

                //not sure if we should remove valueSpan
                default: function() {
                    this.templateData.extraValues.empty();
                    this.templateData.addValueBtn.css( { top: 0 } );
                    window.input_count = 1;
                },

                //set operator to 'in', hide
                // hide value text inputs, show location container
                location: function() {
                    this.showUI.default.call(this);
                    this.templateData.operator.val('in');
                    this.toggleOperatorElements( 'hide' );
                    this.toggleGenericValueInputs( 'hide', [ $('[for="id_value"]') ] );  
                    this.templateData.locationContainer.fadeIn();
                },

                //hide everything, show age slider / label
                age: function() {
                    this.showUI.default.call(this);
                    this.toggleOperatorElements( 'hide' );
                    this.toggleGenericValueInputs( 'hide', [ $('[for="id_value"]') ] );  
                    this.templateData.ageRangeContainer.fadeIn();
                },

                //hide value textboxes, show gender dropdown
                gender: function() {
                    this.showUI.default.call(this);
                    this.templateData.operator.val('eq').attr( 'disabled', true );
                    this.toggleGenericValueInputs( 'hide' );  
                    this.templateData.genderDropdown.fadeIn();
                }
            },
            
            //namespace to clean up old filter type UI before showing new
            cleanupUI: {

                default: function() {
                    this.templateData.extraValues.empty();
                    this.templateData.addValueBtn.css( { top: 0 } );
                    window.input_count = 1;
                    this.templateData.firstValueInput.val('');
                    this.templateData.operator.val('').removeAttr( 'disabled' );
                    this.toggleOperatorElements( 'show' );
                    this.toggleGenericValueInputs( 'show', [ $('[for="id_value"]') ] );
                },

                location: function() {
                    this.cleanupUI.default.call(this);
                    this.templateData.locationTypeDropdown.val('');
                    this.templateData.locationContainer.hide();
                    this.templateData.cityInput.val('');
                    this.templateData.stateInput.val('');
                    this.templateData.cityContainer.hide();
                    this.templateData.stateContainer.hide();
                    this.templateData.addLocationBtn.hide();
                    this.templateData.proposedLocationsContainer.hide();
                    this.templateData.proposedLocations.empty();
                },

                age: function() {
                    this.cleanupUI.default.call(this);
                    this.templateData.ageRangeContainer.hide();
                },

                gender: function() {
                    this.cleanupUI.default.call(this);
                    this.templateData.genderDropdown.val('').hide();
                }
            },
            
            // shows/hides operator UI elements
            toggleOperatorElements: function( func ) {
                var elements = [ this.templateData.operator.prev(), this.templateData.operator ];
                this.toggleElements( elements, func );

                return this;
            },

            // shows/hides filter value UI elements
            toggleGenericValueInputs: function( func, extraEls ) {
                var elements = [ 'firstValueInput', 'extraValues', 'addValueBtn' ];
                if( extraEls ) { elements = elements.concat( extraEls ); }
                this.toggleElements( elements, func );

                return this;
            },

            // shows/hides object elements
            toggleElements: function( elementList, func ) {
                var self = this;
                $.each( elementList, function( i, elReference ) {
                    if( self.templateData[ elReference ] ) {
                        self.templateData[ elReference ][ func ]();
                    } else {
                        elReference[ func ]();
                    }
                } );
                return this;
            },

            close: function() {
                $('#filter-modal').modal('hide');
                
                return this;
            },

        } );

        return filterCreator;
    }
);
