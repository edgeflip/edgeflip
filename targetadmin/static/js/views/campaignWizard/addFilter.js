define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/modal',
      'templates/campaignWizard/addFilter',
      'usStates',
      'css!styles/campaignWizard/addFilter',
      'vendor/jquery-ui',
      'vendor/bootstrap3-typeahead'
    ],
    function( $, _, Backbone, modal, template, usStates ) {

        return new ( Backbone.View.extend( {
            
            events: {
                'click a[data-js="filterType"]': 'showFilterTypeUI',
                'click a[data-js="filterTypeOption"]': 'filterValueSelected',
                'click a[data-js="locationTypeOption"]': 'locationTypeSelected',
                'click button[data-js="addLocationBtn"]': 'addLocationToFilter',
            },

            model: new ( Backbone.Model.extend( { state: undefined } ) )(),

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
                    .initializeAgeSlider();

                this.templateData.locationInput.filter('*[data-type="state"]').typeahead( {
                    source: usStates.values,
                    items: 3
                } );
                
                return this;
            },

            render: function() {

                this.slurpHtml( {
                    template: template(this),
                    insertion: { $el: this.$el } } );

                return this;
            },

            initializeAgeSlider: function() {
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

            shown: function() {

                var self = this;
                
                modal.on( 'confirmed', this.addFilter, this );
                this.delegateEvents();
                modal.templateData.modalContainer.on('hide.bs.modal', function() {
                    modal.off( 'confirmed', self.addFilter ); } );
            },

            showFilterTypeUI: function(e) {

                var clickedEl = $(e.currentTarget);

                this.model.set('state', clickedEl.data('type') );
                this.updateDropdownLabel(e);
                
                this.templateData.filterTypeUI.addClass('hide');
                this.templateData.filterTypeUI.filter( '*[data-type="' + this.model.get('state') + '"]' ).removeClass('hide').fadeIn();
            },

            updateDropdownLabel: function(e) {
               
                var clickedEl = $(e.currentTarget);

                clickedEl.closest('.dropdown').find('*[data-js="dropdownLabel"]').text(clickedEl.text());

                return this;
            },

            filterValueSelected: function(e) {

                this.updateDropdownLabel(e);

                this.model.set( 'value', $(e.currentTarget).data('value') );
            },

            locationTypeSelected: function(e) {

                var clickedEl = $(e.currentTarget);

                this.updateDropdownLabel(e);

                this.templateData.locationInput
                    .addClass('hide')
                    .filter('*[data-type="' + clickedEl.data('value') + '"]')
                        .removeClass('hide').fadeIn();

                this.templateData.addLocationBtn.text( 'Add ' + clickedEl.text() );
            },

            addLocationToFilter: function() {

                var inputEl = this.templateData.locationInput.filter(':visible'),
                    value = $.trim( inputEl.val() );

                if( value && this.templateData.locationContainer.find('span[data-value="' + value + '"]').length === 0 ) {
                    this.templateData.locationContainer.append(
                        $(document.createElement('span'))
                            .addClass('location')
                            .attr('data-value', value)
                            .text(value));

                    if( this.templateData.locationContainer.hasClass('hide') ) {
                        this.templateData.locationContainer.removeClass('hide').fadeIn();
                    }
                }
            },

            addFilter: function() {

                var state = this.model.get('state');

                if( state === 'age' ) {
                    this.availableFilters.add( {
                        feature_type__code: 'age',
                        operator: 'min',
                        value: this.templateData.ageSlider.slider('values')[0]
                    } );
                    this.availableFilters.add( {
                        feature_type__code: 'age',
                        operator: 'max',
                        value: this.templateData.ageSlider.slider('values')[1]
                    } );
                
                    this.trigger('ageFilterCreated');

                } else if( state === 'gender' ) {
                    this.availableFilters.add( {
                        feature_type__code: 'gender',
                        value: this.model.get('value')
                    } );
                } else if( state === 'topic' ) {
                    this.availableFilters.add( {
                        feature_type__code: 'topics',
                        feature: 'topics[' + this.model.get('value') + ']'
                    } );
                }
                
                modal.templateData.modalContainer.modal('hide');
            }

        } ) )();
    }
);
