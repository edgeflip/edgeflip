define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/modal',
      'templates/campaignWizard/addFilter',
      'css!styles/campaignWizard/addFilter',
      'vendor/jquery-ui'
    ],
    function( $, _, Backbone, modal, template ) {

        return new ( Backbone.View.extend( {
            
            events: {
                'click a[data-js="filterType"]': 'showFilterTypeUI',
            },

            model: new ( Backbone.Model.extend( { state: undefined } ) )(),

            initialize: function( options ) {

                _.extend( this, options ); 

                this.filterTypes = [
                    { name: 'age', label: 'Age' },
                    { name: 'gender', label: 'Gender' },
                    { name: 'interest', label: 'Interest' },
                    { name: 'location', label: 'Location' },
                ];

                this.render()
                    .initializeAgeSlider();

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

            showFilterTypeUI: function(e) {
                this.model.set('state',$(e.currentTarget).data('type'));

                this.templateData.filterTypeUI.addClass('hide');
                this.templateData.filterTypeUI.filter( '*[data-type="' + this.model.get('state') + '"]' ).removeClass('hide').fadeIn();
            },

            addFilter: function() {

                var state = this.model.get('state');

                if( state === 'age' ) {
                    this.availableFilters.add( {
                        feature_type__code: 'age',
                        min: this.templateData.ageSlider.slider('values')[0]
                    } );
                    this.availableFilters.add( {
                        feature_type__code: 'age',
                        max: this.templateData.ageSlider.slider('values')[1]
                    } );
                }

                this.trigger('ageFilterCreated');

                modal.templateData.modalContainer.modal('hide');
            }

        } ) )();
    }
);
