//Keep window clean
( function() {

//constructor, the state property tracks currently selected filter type
//  for now, we have a US state dropdown that's populated by a .js file
//  TODO: what should we do when the session times out and this modal
//  shows us a login dialogue ?
var createFilterManager = function() {

    this.state = 'default';

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
        this.usStateDropdown = $('#us-state-dropdown');
        this.cityContainer = $('#city-container');
        this.cityInput = $('#city-input');
        this.stateError = $('#state-error');

        this.genderDropdown = $('#gender-dropdown');

        this.ageRangeContainer = $('#age-range-container');

        return this;
    },

    //bind methods to events on some elements
    //  initialize age range filter slider
    delegateEvents: function() {
        var self = this;

        this.featureDropdown.on( 'change', function() { self.handleFeatureChange() } );
        this.genderDropdown.on( 'change', function() { self.handleGenderChange() } );
        this.usStateDropdown.on( 'change', function() { self.handleUsStateChange() } );

        this.saveChangesBtn.on( 'click', function(e) { e.preventDefault(); self.handleSaveClick(); } );

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

        return this.addFilter[ ( this.addFilter[ this.state ] ) ? this.state : 'generic' ].call( this );
    },

    // namespaced object with the handlers for different feature types for adding filters
    addFilter: {

        //if no city, no worries, if no state, show error and return
        //  creates a city and state filter
        location: function() {

            var cityVal = $.trim( this.cityInput.val() ),
                stateVal = this.usStateDropdown.val();

            if( this.cityContainer.is( ':visible' ) && cityVal != '' ) {
                this.valueInput.val( cityVal );
                this.createFilter( { feature: 'city' } );
            }

            if( stateVal === "" ) { this.stateError.show(); return this; }

            this.valueInput.val( stateVal );
            this.createFilter( { feature: 'state' } );
            this.stateError.hide();
            return this.close();
        },

        //creates two filters, min age, max age based on slider values
        age: function() {

            var values = $( '#age-range' ).slider( 'values' );

            this.operatorDropdown.val('min');
            this.valueInput.val( values[0] );
            this.createFilter();

            this.operatorDropdown.val('max');
            this.valueInput.val( values[1] );
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

    //called when feature type dropdown is changed
    //  cleans up previous UI, shows new UI, sets state
    handleFeatureChange: function() {

        var feature = this.featureDropdown.val();

        this.cleanupUI[ ( this.cleanupUI[ this.state ] ) ? this.state : 'default' ].call( this );
        this.showUI[ ( this.showUI[ feature ] ) ? feature : 'default' ].call( this );

        this.state = feature;

        return this;
    },

    // show/hide city text input if we have a state selected
    handleUsStateChange: function() {

        this.cityContainer[
            ( this.usStateDropdown.val() === '' )
                ? 'fadeOut'
                : 'fadeIn' ]();
        
        return this;
    },

    //namespace to show the proper ui for the filter type
    showUI: {

        //not sure if we should remove valueSpan
        default: function() {
            this.valueSpan.empty();
        },

        //set operator to 'Equal'
        // hide value text inputs, show location container
        location: function() {
            this.showUI.default.call(this);
            this.operatorDropdown.val('eq').attr( 'disabled', true );
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
            this.toggleGenericValueInputs( 'hide' );  
            this.genderDropdown.fadeIn();
        }
    },

    //namespace to clean up old filter type UI before showing new
    cleanupUI: {

        default: function() {
            this.firstValueInput.val('');
            this.operatorDropdown.val('').removeAttr( 'disabled' );
            this.toggleOperatorElements( 'fadeIn' );
            this.toggleGenericValueInputs( 'fadeIn', [ 'valueLabel' ] );
        },

        location: function() {
            this.cleanupUI.default.call(this);
            this.locationContainer.hide();
            this.cityInput.val('');
            this.usStateDropdown.val('');
        },

        age: function() {
            this.cleanupUI.default.call(this);
            this.ageRangeContainer.hide();
        },

        gender: function() {
            this.cleanupUI.default.call(this);
            this.genderDropdown.val('').hide();
        }
    },

    //called when gender dropdown changes
    //   updates the value input so we can call generic add filter
    handleGenderChange: function() {

        this.firstValueInput.val( this.genderDropdown.val() );

        return this;
    },

    //populates us states dropdown for location filter
    addStatesToDropdown: function() {

        var fragment = document.createDocumentFragment()
            placeholder = document.createElement('div');
        
        $.each( usStates, function( i, state ) {
            placeholder.innerHTML = '<option value="' + state + '">' + state + '</option>';
            fragment.appendChild( placeholder.firstChild );
        } );

        this.usStateDropdown.append( fragment );

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

        this.valueInput.val ( filter_values );
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

    //this function was lifted from legacy code
    //  it creates our filter on the client side only
    //  something needs to be doen about that ^
    createFilter: function( opts ) {

        var feature = ( opts && opts.feature ) ? opts.feature : this.featureDropdown.val(),
            operator = this.operatorDropdown.val(),
            filter_values = this.valueInput.val();

        $('#existing-filters').prepend(
            '<div data-filter-id="set_number=' + feature + '.' + operator + 
            '.' + filter_values + '" class="span2 draggable"><p><abbr title="' + 
            feature + ' ' + operator + ' ' + filter_values + '">' + 
            feature + ' ' + ' ' + operator + ' ' + filter_values.slice(0, 15) + 
            '</abbr></p></div>'
        );

        return this;
    },

    //closes modal window
    close: function() {
            
        $('#filter-modal').modal('hide');
        this.featureDropdown.val('');
        this.cleanupUI[ ( this.cleanupUI[ this.state ] ) ? this.state : 'default' ].call( this );

        return this;
    }

} );

new createFilterManager();

} )();
