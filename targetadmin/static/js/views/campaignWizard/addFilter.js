/* Module for Adding a filter in the campaign wizard
   -- currently placed in a bootstrapped modal.  This was a little
   rushed.  It should all work, but its noisy code, not thought
   through enough. */
define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/modal',
      'templates/campaignWizard/addFilter',
      'templates/campaignWizard/singleLocation',
      'usStates',
      'css!styles/campaignWizard/addFilter',
      'vendor/jquery-ui',
      'vendor/bootstrap3-typeahead'
    ],
    function( $, _, Backbone, modal, template, singleLocationHTML, usStates ) {

        return new ( Backbone.View.extend( {
            
            events: {
                'click a[data-js="filterType"]': 'showFilterTypeUI',
                'click a[data-js="filterTypeOption"]': 'filterValueSelected',
                'click a[data-js="locationTypeOption"]': 'locationTypeSelected',
                'click button[data-js="addLocationBtn"]': 'addLocationToFilter',
                'click span[data-js="removeLocationBtn"]': 'removeProposedLocation'
            },

            model: new ( Backbone.Model.extend( { state: undefined } ) )(),

            /* It would be better to have the filter option metadata
               coming back on an ajax request, so we don't need to hardcode
               anything here */
            initialize: function( options ) {

                _.extend( this, options ); 

                this.filterTypeLabel = 'Select Filter Type';

                this.filterTypes = [
                    { name: 'age', label: 'Age' },
                    { name: 'gender', label: 'Gender' },
                    { name: 'topic', label: 'Interest' },
                    { name: 'location', label: 'Location' },
                ];

                this.filterTypeOptions = [
                    { name: 'gender',
                      label: 'Select Gender',
                      options: [
                          { value: 'Female', label: 'Female' },
                          { value: 'Male', label: 'Male' }
                      ]
                    },
                    { name: 'topic',
                      label: 'Select Interest',
                      options: [
                          { value: 'cycling', label: 'Cycling' },
                          { value: 'education', label: 'Education' },
                          { value: 'healthcare', label: 'Healthcare' }
                      ]
                    }
                ];
                
                this.render()
                    .bindAgeSlider() // don't think this is needed
                    .bindStatesTypeahead(); // don't think this is needed

                return this;
            },

            render: function() {

                this.slurpHtml( {
                    template: template(this),
                    insertion: { $el: this.$el } } );

                return this;
            },

            /* jQuery UI slider -- see docs */
            bindAgeSlider: function() {
                var self = this,
                    initialMin = 25,
                    initialMax = 75,
                    getAgeRangeText = function( min, max ) {
                        return "Age Range: " + min + " - " + max };

                this.templateData.ageSlider.slider( {
                    range: true,
                    min: 0,
                    max: 100,
                    values: [ initialMin, initialMax ],
                    slide: function( event, ui ) {
                      self.templateData.ageRangeDisplay.text( getAgeRangeText( ui.values[0], ui.values[1] ) );
                    }
                } );

                this.templateData.ageRangeDisplay.text( getAgeRangeText( initialMin, initialMax ) );

                return this;
            },

            /* bootstrap3 typeahead plugin, not from bootstrap, but some dude */
            bindStatesTypeahead: function() {

                this.templateData.locationInput.filter('*[data-type="state"]').typeahead( {
                    source: usStates.values,
                    items: 3
                } );

                return this;
            },

            /* called when modal is shown, this should be fired on a listener instead
               of directly called by the filters campaign view */
            shown: function() {

                var self = this;
                
                modal.on( 'confirmed', this.addFilter, this );

                this.delegateEvents()
                    .bindAgeSlider()
                    .bindStatesTypeahead();

                modal.templateData.modalContainer.on('hide.bs.modal', function() {
                    modal.off( 'confirmed', self.addFilter ); } );
            },

            /* Filter type has been selected, show the proper UI */
            showFilterTypeUI: function(e) {

                var clickedEl = $(e.currentTarget);

                this.model.set('state', clickedEl.data('type') );
                this.updateDropdownLabel(e);
                
                this.templateData.filterTypeUI.addClass('hide');
                this.templateData.filterTypeUI.filter( '*[data-type="' + this.model.get('state') + '"]' ).removeClass('hide').fadeIn();
            },

            /* After a dropdown value has been selected, updated the text shown */
            updateDropdownLabel: function(e) {
               
                var clickedEl = $(e.currentTarget);

                clickedEl.closest('.dropdown').find('*[data-js="dropdownLabel"]').text(clickedEl.text());

                return this;
            },

            /* Called when a filter value has been selected (male,female) */
            filterValueSelected: function(e) {

                this.updateDropdownLabel(e);

                this.model.set( 'value', $(e.currentTarget).data('value') );
            },

            /* Show either state, or city location input */
            locationTypeSelected: function(e) {

                var clickedEl = $(e.currentTarget);

                this.model.set('locationType', clickedEl.data('value'));

                this.updateDropdownLabel(e);

                this.templateData.locationInput
                    .addClass('hide')
                    .filter('*[data-type="' + clickedEl.data('value') + '"]')
                        .removeClass('hide').fadeIn();

                this.templateData.addLocationBtn.text( 'Add ' + clickedEl.text() );
            },

            /* location added, put it in box, to await others joining */
            addLocationToFilter: function() {

                var inputEl = this.templateData.locationInput.filter(':visible'),
                    value = $.trim( inputEl.val() );

                if( value && this.templateData.locationContainer.find('li[data-value="' + value + '"]').length === 0 ) {
                    this.templateData.locationContainer.append( singleLocationHTML( { value: value } ) );

                    if( this.templateData.locationContainer.hasClass('hide') ) {
                        this.templateData.locationContainer.removeClass('hide').fadeIn();
                    }
                }
            },

            /* location removed, remove it from box
                potential bug: should remove location after fadeOut */
            removeProposedLocation: function(e) {
                $(e.currentTarget).parent().fadeOut();    

                if( this.templateData.locationContainer.children().length === 0 ) {
                    this.templateData.locationContainer.addClass('hide');
                }
            },

            /* user clicks add filter, so we create a filter model based on the
               options selected, the rest is handled by the filters campaign view */
            addFilter: function() {

                var state = this.model.get('state');

                switch (this.model.get('state')) {
                    case 'age':
                        this.availableFilters.add( {
                            feature_type__code: 'age',
                            feature: 'age',
                            operator: 'min',
                            value: this.templateData.ageSlider.slider('values')[0]
                        } );
                        this.availableFilters.add( {
                            feature_type__code: 'age',
                            feature: 'age',
                            operator: 'max',
                            value: this.templateData.ageSlider.slider('values')[1]
                        } );
                        this.trigger('ageFilterCreated');
                        break;
                    case 'gender':
                        this.availableFilters.add( {
                            feature_type__code: 'gender',
                            feature: 'gender',
                            value: this.model.get('value')
                        } );
                        break;
                    case 'topic':
                        this.availableFilters.add( {
                            feature_type__code: 'topics',
                            feature: 'topics[' + this.model.get('value') + ']'
                        } );
                        break;
                    case 'location':
                        this.availableFilters.add( {
                            feature_type__code: this.model.get('locationType'),
                            feature: this.model.get('locationType'),
                            value: _.map( this.templateData.locationContainer.children(), function(locationEl) {
                                return $(locationEl).find('*[data-js="value"]').text();
                            }, this ).join('||')
                        } );
                        break;
                }

                modal.templateData.modalContainer.modal('hide');
            }

        } ) )();
    }
);