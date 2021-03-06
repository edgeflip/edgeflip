//Keep window clean
( function() {

//constructor, the state property tracks currently selected filter type
//  for now, we have a US state dropdown that's populated by a .js file
//  TODO: what should we do when the session times out and this modal
//  shows us a login dialogue ?
var createFilterManager = function() {

    this.state = 'default';
    this.locationState = '';

    this.cacheDomElements();

    this.delegateEvents();

    this.addStatesToDropdown();

    return this;
}

//add methods to our class
$.extend( createFilterManager.prototype, {


    //hopefully in the future we can move to a templating engine
    // that plays nicely with django and javascript -- i think mustache/handlebars
    // should do the job, then we will never need a function like this again
    cacheDomElements: function() {

        this.featureDropdown =  $('#id_feature');
        this.featureError =  $('#feature-error');
        
        this.operatorDropdown = $('#id_operator');
        this.operatorLabel = $('label[for="id_operator"]');
        this.operatorError = $('#operator-error');

        this.valueLabel = $('label[for="id_value"]');
        this.firstValueInput = $('#id_value-split-1');
        this.valueSpan = $('#value-span');
        this.valueError = $('#value-error');
        this.addValueIcon = $('#value-a');
        this.valueInput = $('#id_value');

        this.saveChangesBtn = $('#filter-add');

        this.locationContainer = $('#location-options-container');
        this.locationTypeDropdown = $('#location-type-dropdown');
        this.addLocationFilterButton = $('#add-location-filter');
        this.countryInput = $('#country-dropdown');
        this.stateInput = $('#state-input');
        this.cityContainer = $('#city-container');
        this.stateContainer = $('#state-container');
        this.countryContainer = $('#country-container');
        this.cityInput = $('#city-input');
        this.stateError = $('#state-error');

        this.locationFilterView = $('#location-filter-view'); 
        this.locationFilters = $('#location-filters'); 

        this.genderDropdown = $('#gender-dropdown');

        this.interestDropdown = $('#interest-dropdown');

        this.ageRangeContainer = $('#age-range-container');

        return this;
    },

    //bind methods to events on some elements
    //  initialize age range filter slider
    delegateEvents: function() {
        var self = this;

        this.featureDropdown.on( 'change', function() { self.handleFeatureChange() } );
        this.genderDropdown.on( 'change', function() { self.handleGenderChange() } );
        this.interestDropdown.on( 'change', function() { self.handleInterestChange() } );

        this.locationTypeDropdown
            .on( 'change', function() { self.handleLocationTypeChange() } )
            .popover( { trigger: 'manual' } );

        this.addLocationFilterButton.on( 'click', function(e) { self.handleAddLocationClick(e); return false; } );
        this.addLocationFilterButton.popover( { trigger: 'manual' } );
        

        this.locationFilterView.on( 'click', '.remove-filter-item', function(e) { self.removeLocationFilter(e); } );

        this.saveChangesBtn.on( 'click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            self.handleSaveClick();
            return false;
        } );

        $('#filter-modal').on( 'hide', function(e) { self.cleanUpModal(e); } );

        $( "#age-range" ).slider( {
            range: true,
            min: 0,
            max: 100,
            values: [ 25, 75 ],
            slide: function( event, ui ) {
              $( "#age-range-display" ).text( ui.values[ 0 ] + " - " + ui.values[ 1 ] );
            }
        } );
        
        return this;
    },

    //called when "Save Changes" is clicked
    //  if we have a special handler for the feature type, call it, else use the generic add filter
    handleSaveClick: function() {

        return this.filterHandlers[ ( this.filterHandlers[ this.state ] ) ? this.state : 'generic' ].call( this );
    },

    // namespaced object with the handlers for different feature types for adding filters
    filterHandlers: {

        location: function() {
            var self = this,
                filters = this.locationFilters.children();

            if( ! this.locationTypeDropdown.val() ) {
                this.locationTypeDropdown.popover('show');
                this.delegateRemovePopover( this.locationTypeDropdown );
                return;
            }

            if( filters.length === 0 ) {
                this.addLocationFilterButton.click();
                filters = this.locationFilters.children();
                return;
            }

            filters.each( function( i, filterEl ) {
                var new_id = 'id_value-split-' + parseInt( i + 1 );
                if( i === 0 ) { self.firstValueInput.val( $(filterEl).data('val') ); }
                else {
                    self.valueSpan.append(    
                        $('<input id="' + new_id + '" name="' + new_id + '" type="text" class="filter-val-input">').val( $(filterEl).data('val') )
                    );
                }
            } );

            this.setFilterValue();
            this.operatorDropdown.val('in');
            this.createFilter( { feature: this.locationState } );

            return this.close();
        },

        //creates two filters, min age, max age based on slider values
        age: function() {

            var values = $( '#age-range' ).slider( 'values' );

            if( values[0] !== 0 &&
                values[1] !== 100 ) {

                this.createAgeFilter( values[0], values[1] );

            } else {

                if( values[0] == 0 ) {
                    this.operatorDropdown.val('max');
                    this.valueInput.val( values[1] );
                    this.createFilter();
                } else {
                    this.operatorDropdown.val('min');
                    this.valueInput.val( values[0] );
                    this.createFilter();
                }
            }

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

    //called when feature type dropdown is changed
    //  cleans up previous UI, shows new UI, sets state
    handleFeatureChange: function() {

        var feature = this.featureDropdown.val();

        if( feature != '' && this.featureError.is(':visible') ) {
            this.featureError.hide();
        }

        this.cleanupUI[ ( this.cleanupUI[ this.state ] ) ? this.state : 'default' ].call( this );
        this.showUI[ ( this.showUI[ feature ] ) ? feature : 'default' ].call( this );

        this.state = feature;

        return this;
    },

    handleLocationTypeChange: function() {

        var locationType = this.locationTypeDropdown.val(),
            capitalizedLocationType = locationType.charAt(0).toUpperCase() + locationType.slice(1);

        if( this.locationState ) {
            $('#' + this.locationState + '-container').hide();
        }

        $('#' + locationType + '-container').fadeIn();

        if( locationType ) {
            this.addLocationFilterButton
                .text( 'Add ' + capitalizedLocationType )
                .fadeIn();
        } else {
            
            this.addLocationFilterButton.hide();
        }

        this.locationState = locationType;

        this.locationFilterView.hide();
        this.locationFilters.empty();

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

    handleAddLocationClick: function(e) {

        var input = this[ this.locationState + 'Input' ],
            val = $.trim( input.val() ),
            self = this;

        var text = ( input.prop('tagName') === 'SELECT' )
            ? $( input.find('option[value="' + val + '"]') ).text()
            : val;

        if( val === '' ) { return; }

        this.locationFilterView.fadeIn();

        if( ( this.stateContainer.is(':visible') ) &&
            ( ! _.contains( usStates, val ) ) ) {

            e.stopPropagation();

            this.addLocationFilterButton.attr( 'data-content', 'Invalid State' ).popover('show');
            this.delegateRemovePopover( this.addLocationFilterButton );
            return;
        }

        if( this.locationFilters.children().length ) {

            if( this.locationFilters.find( 'div[data-val="' + val + '"]' ).length ) {

                e.stopPropagation();

                this.addLocationFilterButton.attr( 'data-content', 'This filter has already been added' ).popover('show');
                this.delegateRemovePopover( this.addLocationFilterButton );
                return;
            }

            $('<div class="filter-or">or</div>').appendTo( this.locationFilters );
        }

        $('<div class="clearfix" data-val="' + val + '"><div class="location-filter-value">' + text + '</div><div class="remove-filter-item"><i class="icon-remove"></i></div>').appendTo( this.locationFilters );

        input.val('');
    },

    removeLocationFilter: function( e ) {
        var row = $( $( e.currentTarget ).parent() ),
            prevEl = row.prev('.filter-or'),
            nextEl = row.next('.filter-or');

        if( prevEl.length ) { prevEl.fadeOut( 400, function() { prevEl.remove(); } ); }
        else if( nextEl.length ) { nextEl.fadeOut( 400, function() { nextEl.remove(); } ); }

        row.fadeOut( 400, function() { row.empty().remove() } );
    },

    //namespace to show the proper ui for the filter type
    showUI: {

        //not sure if we should remove valueSpan
        default: function() {
            this.valueSpan.empty();
            $('.add-input-container').css( { top: 0 } );
            window.input_count = 1;
        },

        //set operator to 'in', hide
        // hide value text inputs, show location container
        location: function() {
            this.showUI.default.call(this);
            this.operatorDropdown.val('in');
            this.toggleOperatorElements( 'hide' );
            this.toggleGenericValueInputs( 'hide', [ 'valueLabel' ] );  
            this.locationContainer.fadeIn();
        },

        //hide everything, show age slider / label
        age: function() {
            this.showUI.default.call(this);
            this.toggleOperatorElements( 'hide' );
            this.toggleGenericValueInputs( 'hide', [ 'valueLabel' ] );  
            this.ageRangeContainer.fadeIn();
        },

        //hide value textboxes, show gender dropdown
        gender: function() {
            this.showUI.default.call(this);
            this.operatorDropdown.val('eq').attr( 'disabled', true );
            this.toggleOperatorElements( 'hide' );
            this.toggleGenericValueInputs( 'hide' );  
            this.genderDropdown.fadeIn();
        },

        interest: function() {
            this.showUI.default.call(this);
            this.operatorDropdown.val('eq').attr( 'disabled', true );
            this.toggleOperatorElements( 'hide' );
            this.toggleGenericValueInputs( 'hide' );
            this.interestDropdown.fadeIn();
        }
    },

    //namespace to clean up old filter type UI before showing new
    cleanupUI: {

        default: function() {
            this.valueSpan.empty();
            $('.add-input-container').css( { top: 0 } );
            window.input_count = 1;
            this.firstValueInput.val('');
            this.operatorDropdown.val('').removeAttr( 'disabled' );
            this.toggleOperatorElements( 'hide' );
            this.toggleGenericValueInputs( 'hide', [ 'valueLabel' ] );
        },

        location: function() {
            this.cleanupUI.default.call(this);
            this.locationTypeDropdown.val('');
            this.locationContainer.hide();
            this.countryInput.val('');
            this.cityInput.val('');
            this.stateInput.val('');
            this.cityContainer.hide();
            this.stateContainer.hide();
            this.countryContainer.hide();
            this.addLocationFilterButton.hide();
            this.locationFilterView.hide();
            this.locationFilters.empty();
        },

        age: function() {
            this.cleanupUI.default.call(this);
            this.ageRangeContainer.hide();
        },

        gender: function() {
            this.cleanupUI.default.call(this);
            this.genderDropdown.val('').hide();
        },

        interest: function() {
            this.cleanupUI.default.call(this);
            this.interestDropdown.val('').hide();
        }
    },

    //called when gender dropdown changes
    //   updates the value input so we can call generic add filter
    handleGenderChange: function() {

        this.firstValueInput.val( this.genderDropdown.val() );

        return this;
    },

    handleInterestChange: function() {
        this.firstValueInput.val(this.interestDropdown.val());
        return this;
    },

    //populates us states dropdown for location filter
    addStatesToDropdown: function() {

        this.stateInput.typeahead( {
             source: usStates,
             items: 3
        } );

        return this;
    },

    // shows/hides operator UI elements
    toggleOperatorElements: function( func ) {
        var elements = [ 'operatorLabel', 'operatorDropdown', 'operatorError' ];
        if( func === 'fadeIn' || func === 'show' ) { elements.splice( elements.indexOf( 'operatorError' ), 1 ); }
        this.toggleElements( elements, func );

        return this;
    },

    // shows/hides filter value UI elements
    toggleGenericValueInputs: function( func, extraEls ) {
        var elements = [ 'firstValueInput', 'valueSpan', 'addValueIcon', 'valueError' ];
        if( func === 'fadeIn' || func === 'show' ) { elements.splice( elements.indexOf( 'valueError' ), 1 ); }
        if( extraEls ) { elements = elements.concat( extraEls ); }
        this.toggleElements( elements, func );

        return this;
    },

    // shows/hides object elements
    toggleElements: function( elementList, func ) {
        var self = this;
        $.each( elementList, function( i, elReference ) { self[ elReference ][ func ](); } );
        return this;
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

        this.valueInput.val( filter_values );
    },

    //this function was lifted from legacy code
    //  it validates our inputs
    isValid: function() {

        var validation_elems = [
            [ 'featureDropdown', 'featureError' ],
            [ 'operatorDropdown', 'operatorError' ],
            [ 'valueInput', 'valueError' ] ],

            isValid = true;

        for(var elem=0; elem < validation_elems.length; elem++) {
            if( this[ validation_elems[elem][0] ].val() === "" ) {
                this[ validation_elems[elem][1] ].show();
                isValid = false;
            } else {
                this[ validation_elems[elem][1] ].hide();
            }
        }

        return isValid;
    },

    createFilter: function( opts ) {
        var feature = ( opts && opts.feature ) ? opts.feature : this.featureDropdown.val(),
            operator = this.operatorDropdown.val(),
            filter_values = this.valueInput.val(),
            filterEl =
                $('<div title="' + feature + ' ' + operator + ' ' + filter_values + '" data-filter-id="set_number=' + feature + '.' + operator + 
                '.' + filter_values + '" class="span2 draggable"><div class="filter-content-container"><span class="filter">' +
                feature + ' ' + ' ' + operator + ' ' + filter_values + 
                '</span></div></div>');

        $('#existing-filters').prepend( window.filterCleaner.cleanFilter(filterEl) );

        if( opts && opts.hide ) { filterEl.hide(); }
        if( opts && opts.link ) { filterEl.attr('data-link',opts.link); }

        return this;
    },

    createAgeFilter: function( min, max ) {
        var text = "age: between " + min + " and " + max,
            link = min + '-' + max,
            filterEl =
                $('<div title="' + text + '" class="span2 draggable"><div class="filter-content-container"><span class="filter">' +
                text + '</span></div></div>');

        filterEl.attr('data-link',link);

        this.operatorDropdown.val('min');
        this.valueInput.val( min );
        this.createFilter( { hide: true, link: link } );

        this.operatorDropdown.val('max');
        this.valueInput.val( max );
        this.createFilter( { hide: true, link: link } );
        
        $('#existing-filters').prepend( filterEl );
    },

    //closes modal window
    close: function() {
        $('#filter-modal').modal('hide');
        this.cleanUpModal();
        
        return this;
    },

    cleanUpModal: function(e) {
        if( e && $(e.target).attr('data-content') ) { return; }
        this.featureDropdown.val('');
        this.cleanupUI[ ( this.cleanupUI[ this.state ] ) ? this.state : 'default' ].call( this );
        this.state = 'default';
    }

} );

new createFilterManager();

} )();
