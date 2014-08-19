define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'models/filters',
      'views/modal',
      'views/campaignWizard/addFilter',
      'templates/campaignWizard/filters',
      'templates/campaignWizard/filterLayer',
      'templates/campaignWizard/filtersInfo',
      'templates/campaignWizard/filter',
      'css!styles/campaignWizard/filters',
    ],
    function( $, _, Backbone, FilterCollection, modal, addFilter, template, filterLayerTemplate, filtersInfoTemplate, filterTemplate ) {

        return Backbone.View.extend( {
            
            events: {
                'click *[data-js="moreInfoBtn"]': 'showFilterInfo',
                'click *[data-js="emptyFallbackHelpBtn"]': 'showEmptyFallbackInfo',
                'click *[data-js="addFilterBtn"]': 'showAddFilter',
                'click *[data-js="addFallbackBtn"]': 'addFallbackLayer',
                'click *[data-js="removeLayerBtn"]': 'removeLayer',
                'dblclick *[data-js="filter"]': 'moveFilter',
                'click *[data-js="nextStep"]': 'triggerNextStep'
            },

            initialize: function( options ) {

                _.extend( this, options ); 

                //makes ajax call to get filters
                this.availableFilters = 
                addFilter.availableFilters = new FilterCollection(
                    [ ], 
                    { clientId: this.model.get('clientId') } 
                ).on( 'add', this.addAvailableFilter, this );

                this.model.set('filterLayerCount',1);
                this.model.on('change:name', this.updateName, this );
                addFilter.on('ageFilterCreated', this.updateAgeFilterUI, this );

                this.render();

                this.addDraggableFunctionality();
                

                return this;
            },

            render: function() {

                if( this.hide ) { this.$el.hide(); }

                this.slurpHtml( {
                    template: template( this.model.toJSON() ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                this.renderFilters();

                return this;
            },

            renderFilters: function() {

                this.availableFilters.fetch();

                if( ! this.model.has('filters') ) {

                    this.slurpHtml( {
                        template: filterLayerTemplate( {
                            label: 'Target Audience',
                            removeBtn: false
                        } ),
                        insertion: { $el: this.templateData.enabledFiltersContainer }
                    } );
                }
            },

            addAvailableFilter: function(filter) {

                this.templateData.availableFilters.append(
                    filterTemplate( _.extend( {}, filter.toJSON(), { readable: filter.getReadable() } ) )
                );
            },

            addFallbackLayer: function(e) {

                var clickedButton = $(e.currentTarget);

                if( this.model.get('filterLayerCount') === 4 ) { return; }

                clickedButton.fadeOut();

                this.slurpHtml( {
                    template: filterLayerTemplate( {
                        label: 'Fallback Audience ' + ( this.model.get('filterLayerCount') ),
                        removeBtn: true,
                        disableAddBtn: ( this.model.get('filterLayerCount') === 3 ) ? true: false
                    } ),
                    insertion: { $el: this.templateData.enabledFiltersContainer }
                } );

                //copy filters to new layer
                clickedButton.closest('*[data-target="filterLayer"]')
                                .find('*[data-js="filterContainer"]').children().clone(true).appendTo(
                    this.templateData.enabledFiltersContainer.children().last().find('*[data-js="filterContainer"]') );

                this.model.set('filterLayerCount', this.model.get('filterLayerCount') + 1 );

                this.addDraggableFunctionality();

                return this;
            },

            filterReceived: function( event, ui ) {
                var dataLink = ui.item.attr('data-link');
                if( dataLink ) {
                    ui.sender.find('[data-link="' + dataLink + '"]').appendTo( $(event.target) );
                }
            },

            addDraggableFunctionality: function() {

                var sortableElements = this.$el.find('*[data-type="sortable"]');

                sortableElements.sortable( {
                    connectWith: sortableElements,
                    receive: this.filterReceived
                } ).disableSelection();

                return this;
            },

            moveFilter: function(e) {

                var dblClickedFilter = $(e.currentTarget);
                
                if( dblClickedFilter.closest( this.templateData.availableFilters ).length ) {
                    dblClickedFilter.appendTo(
                        this.templateData.enabledFiltersContainer.children().last().find('*[data-js="filterContainer"]')
                    );
                } else {
                    dblClickedFilter.appendTo( this.templateData.availableFilters );
                }
            },

            removeLayer: function(e) {
                
                var layerContainer = $(e.currentTarget).closest('*[data-target="filterLayer"]'),
                    self = this;
                
                if( layerContainer.find('*:visible[data-js="addFallbackBtn"]').length ) {
                    layerContainer.prev().find('*[data-js="addFallbackBtn"]').show();
                }

                //make sure we aren't remove a filter that doesn't exist elsewhere
                _.each( layerContainer.find('*[data-js="filterContainer"]').children(), function( filter ) {
                    filter = $(filter);
                    if( this.$el.find('*[data-filter-id="' + $(filter).attr('data-filter-id') + '"]').length === 1 ) {
                        filter.appendTo( this.templateData.availableFilters );
                    }
                }, this );


                layerContainer.fadeOut( 400, function() {
                    $(this).remove();
                    self.updateFallbackLabels();
                } );
                
                this.model.set('filterLayerCount', this.model.get('filterLayerCount') - 1 );
            },

            updateFallbackLabels: function() {

                _.each( this.templateData.enabledFiltersContainer.children(), function( filterLayerContainer, i ) {
                    if( i === 0 ) { return; }
                    $(filterLayerContainer).find('*[data-target="filter-label"]').text( 'Fallback Audience ' + i);
                }, this );
                
            },

            updateName: function() {
                this.templateData.campaignName.text( this.model.get('name') );
            },

            showFilterInfo: function() {
                modal.update( {
                    body: filtersInfoTemplate,
                    longContent: true
                  } );

                modal.templateData.confirmBtn.hide();
                modal.templateData.modalContainer.modal();
                
            },

            showEmptyFallbackInfo: function() {
                modal.update( {
                    body: filtersInfoTemplate,
                  } );

                modal.templateData.modalContainer.find('p[data-js="target-audience"]').hide();
                modal.templateData.modalContainer.find('p[data-js="fallback-audience"]').hide();
                modal.templateData.confirmBtn.hide();
                modal.templateData.modalContainer.modal();
            },

            showAddFilter: function() {

                modal.update( {
                    body: addFilter.$el,
                    title: 'Filter Type',
                    confirmText: 'Add Filter',
                    showCloseBtn: true
                } );

                modal.templateData.modalContainer.modal();

                addFilter.shown();
            },
            
            updateAgeFilterUI: function() {

                var min = this.availableFilters.at( this.availableFilters.length - 2 ).get('min'),
                    max = this.availableFilters.at( this.availableFilters.length - 1 ).get('max'),
                    availableFiltersCount = this.templateData.availableFilters.children().length,
                    combinedAgeFilter = $( filterTemplate( { readable: 'Between ' + min + ' and ' + max } ) );

                combinedAgeFilter.attr('data-link',min + '-' + max);

                _.each( [ availableFiltersCount - 2, availableFiltersCount - 1 ], function( i ) {
                    $( this.templateData.availableFilters.children()[ i ] )
                      .hide()
                      .attr('data-link',min + '-' + max);
                }, this );

                this.templateData.availableFilters.append( combinedAgeFilter );
            },

            triggerNextStep: function() {
                this.trigger('nextStep');
            }

        } );
    }
);
