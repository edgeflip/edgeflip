/* Module for the Filters section of the Campaign Wizard.
   Too many templates for one view -- perhaps they should
   go into their own module */
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
  
            /* see templates for more information */
            events: {
                'click *[data-js="moreInfoBtn"]': 'showFilterInfo',
                'click *[data-js="emptyFallbackHelpBtn"]': 'showEmptyFallbackInfo',
                'click *[data-js="addFilterBtn"]': 'showAddFilter',
                'click *[data-js="addFallbackBtn"]': 'addFallbackLayer',
                'click *[data-js="removeLayerBtn"]': 'removeLayer',
                'dblclick *[data-js="filter"]': 'moveFilter',
                'click *[data-js="nextStep"]': 'prepareFormFieldValues',
                'click *[data-js="prevStep"]': 'goBack'
            },

            initialize: function( options ) {

                _.extend( this, options ); 

                /* Whenever a filter is added to the collection addAvailableFilter will be invoked. */
                this.availableFilters = 
                addFilter.availableFilters = new FilterCollection(
                    [ ], 
                    { clientId: this.model.get('clientId') } 
                ).on( 'add', this.addAvailableFilter, this );

                /* If we are editing a campaign, update the UI to show the current filters
                   enabled. */
                if( this.campaignModel ) {
                    this.availableFilters.on( 'sync', this.reflectCampaignState, this );
                }

                this.model.set('filterLayerCount',1);
                this.model.on('change:name', this.updateName, this );
                addFilter.on('ageFilterCreated', this.updateAgeFilterUI, this );

                this.render();

                this.addDraggableFunctionality();

                return this;
            },

            /* slurp and insert out main template, */
            render: function() {

                if( this.hide ) { this.$el.hide(); }

                this.slurpHtml( {
                    template: template( this.model.toJSON() ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                this.renderFilters();

                return this;
            },

            renderFilters: function() {

                /* (backbone.model) send an ajax request for the filters */
                this.availableFilters.fetch();

                /* I don't think this if statement is needed */ 
                if( ! this.model.has('filters') ) {

                    this.slurpHtml( {
                        template: filterLayerTemplate( {
                            label: 'Target Audience',
                            removeBtn: false,
                            count: 1
                        } ),
                        insertion: { $el: this.templateData.enabledFiltersContainer }
                    } );
                }
            },

            /* Adds a client filter into the Available Filter box */
            addAvailableFilter: function(filter) {

                this.templateData.availableFilters.append(
                    filterTemplate( _.extend( {}, filter.toJSON(), { readable: filter.getReadable() } ) )
                );
            },

            /* Add fallback button is clicked */
            addFallbackLayer: function(e) {

                var clickedButton = $(e.currentTarget);

                if( this.model.get('filterLayerCount') === 4 ) { return; }

                clickedButton.fadeOut();

                this.slurpHtml( {
                    template: filterLayerTemplate( {
                        label: 'Fallback Audience ' + ( this.model.get('filterLayerCount') ),
                        removeBtn: true,
                        count: this.model.get('filterLayerCount'),
                        disableAddBtn: ( this.model.get('filterLayerCount') === 3 ) ? true: false
                    } ),
                    insertion: { $el: this.templateData.enabledFiltersContainer }
                } );

                //copy filters to new layer
                clickedButton.closest( this.templateData.filterLayer )
                                .find('*[data-js="filterContainer"]').children().clone(true).appendTo(
                    this.templateData.enabledFiltersContainer.children().last().find('*[data-js="filterContainer"]') );

                this.model.set('filterLayerCount', this.model.get('filterLayerCount') + 1 );
                this.updateFallbackLabels();

                this.addDraggableFunctionality();

                return this;
            },

            /* Called when a filter is moved from one layer to another, or back to the available
               filters container.  This is a hack to handle age filters.  On the back end it is
               two existing filters, on the front, it is one filter for display with two associated
               filters hiding for the backend */
            filterReceived: function( event, ui ) {
                var dataLink = ui.item.attr('data-link');
                if( dataLink ) {
                    ui.sender.find('[data-link="' + dataLink + '"]').appendTo( $(event.target) );
                }
            },

            /* jQuery ui draggable (sortable) stuff */
            addDraggableFunctionality: function() {

                var sortableElements = this.$el.find('*[data-type="sortable"]');

                sortableElements.sortable( {
                    connectWith: sortableElements,
                    receive: this.filterReceived
                } ).disableSelection();

                return this;
            },

            /* handles double click on a filter */
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

            /* 'X' (remove layer) is clicked */ 
            removeLayer: function(e) {
                
                var layerContainer = $(e.currentTarget).closest('*[data-js="filterLayer"]'),
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

            /* after a layer removal make sure the labels still make sense ( numbers ) */
            updateFallbackLabels: function() {

                _.each( this.templateData.enabledFiltersContainer.children(), function( filterLayerContainer, i ) {
                    if( i === 0 ) { return; }
                    $(filterLayerContainer).find('*[data-target="filterLabel"]').text( 'Fallback Audience ' + i);
                    $(filterLayerContainer).find('*[data-target="filterLayerFormField"]').attr(
                        'name', 'enabled-filters-' + ( i + 1 ) );
                }, this );
                
            },

            /* should be in base class, updates campaign name in header if it changes */
            updateName: function() {
                this.templateData.campaignName.text( this.model.get('name') );
            },

            /* Potential bug: 'filterLayerCount' should be updated here */
            /* Adds current campaign filter state to ui */
            reflectCampaignState: function() {
                var campaignFilters = this.campaignModel.get('filters');
                _.each( campaignFilters, function( filterLayer, i ) {
                    _.each( filterLayer, function( filter ) {
                        var selector = '*[data-filter-id="set_number=' + filter.feature + '.' + filter.operator + '.' + filter.value + '"]',
                            fromAvailable = this.templateData.availableFilters.find( selector );

                        if( fromAvailable.length ) { fromAvailable.dblclick(); }
                        else {
                            this.templateData.enabledFiltersContainer
                              .find( selector ).clone(true).first().appendTo( this.templateData.availableFilters ).dblclick();
                        }
                    }, this );

                    if( campaignFilters.length - 1 != i && campaignFilters[i+1].length != 0 ) {
                        this.templateData.addFallbackBtn.click();
                        this.templateData.filterContainer.last().empty();
                    }
                }, this );
            },

            /* shows modal with information regarding how filters work */ 
            showFilterInfo: function() {
                modal.update( {
                    body: filtersInfoTemplate,
                    longContent: true
                  } );

                modal.templateData.confirmBtn.hide();
                modal.templateData.modalContainer.modal();
                
            },

            /* shows modal with information regarding how empty fallbacks work */ 
            showEmptyFallbackInfo: function() {
                modal.update( {
                    body: filtersInfoTemplate,
                  } );

                modal.templateData.modalContainer.find('p[data-js="target-audience"]').hide();
                modal.templateData.modalContainer.find('p[data-js="fallback-audience"]').hide();
                modal.templateData.confirmBtn.hide();
                modal.templateData.modalContainer.modal();
            },

            /* shows modal with add filter view as content */ 
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
           
            /* Handles the age filter hack (described above) when an age filter is created */
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

            /* translates filters into input element value for the backend to handle before
               heading to the next step this format was not done by cbaron, it is not good */
            prepareFormFieldValues: function() {

                _.each( _.range( 1, this.model.get('filterLayerCount') + 1 ), function( i ) {

                    var layerContainer = $(this.templateData.filterLayer[i-1]);

                    layerContainer.find('input[name="enabled-filters-' + i + '"]').val(
                        _.map( layerContainer.find('*[data-js="filterContainer"]').children(), function( filter ) {
                            return '"' + $(filter).attr('data-filter-id').split('=')[1] + '"';
                        }, this )
                    );
                }, this );

                this.trigger('nextStep');
            },

            /* back is clicked */
            goBack: function() {
                this.trigger('previousStep');
            }

        } );
    }
);
