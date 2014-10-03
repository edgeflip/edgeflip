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

            initialize: function (options) {
                _.extend(this, options);

                this.maxCount = 4;
                this.maxIndex = this.maxCount - 1;

                /* Whenever a filter is added to the collection addAvailableFilter will be invoked. */
                this.availableFilters = 
                addFilter.availableFilters = new FilterCollection(
                    [],
                    {clientId: this.model.get('clientId')}
                ).on('add', this.addAvailableFilter, this);

                /* If we are editing a campaign, update the UI to show the current filters
                   enabled. */
                if(this.campaignModel) {
                    this.model.set('noEmptyFallback', !this.campaignModel.get('include_empty_fallback'));
                    this.availableFilters.on('sync', this.reflectCampaignState, this);
                }

                this.model.set('filterLayerCount', 1);
                this.model.on('change:name', this.updateName, this);
                addFilter.on('ageFilterCreated', this.updateAgeFilterUI, this);

                this.render();
                this.addDraggableFunctionality();
                return this;
            },

            /* slurp and insert out main template, */
            render: function() {
                if(this.hide) {this.$el.hide();}
                this.slurpHtml({
                    template: template(this.model.toJSON()),
                    insertion: {$el: this.$el.appendTo(this.parentEl)}
                });
                this.renderFilters();
                return this;
            },

            renderFilters: function() {
                /* (backbone.model) send an ajax request for the filters */
                this.availableFilters.fetch();

                if (!this.model.has('filters')) {
                    this.slurpHtml({
                        template: filterLayerTemplate({
                            label: 'Target Audience',
                            removeBtn: false,
                            count: 1
                        }),
                        insertion: {$el: this.templateData.enabledFiltersContainer}
                    });
                }
            },

            /* Adds a client filter into the Available Filter box */
            addAvailableFilter: function(filter) {
                this.templateData.availableFilters.append(
                    filterTemplate(_.extend({}, filter.toJSON(), {readable: filter.getReadable()}))
                );
            },

            addFallbackLayer: function(event) {
                /* Add fallback button is clicked */
                return this._addFallbackLayer($(event.currentTarget));
            },

            _addFallbackLayer: function(clickedButton) {
                var filters,
                    filterLayerCount = this.model.get('filterLayerCount');

                clickedButton = clickedButton || this.templateData.addFallbackBtn;

                if (filterLayerCount === this.maxCount) {return;}

                clickedButton.fadeOut();
                this.slurpHtml({
                    template: filterLayerTemplate({
                        label: 'Fallback Audience ' + filterLayerCount,
                        removeBtn: true,
                        count: filterLayerCount
                    }),
                    insertion: {$el: this.templateData.enabledFiltersContainer}
                });

                /* copy filters to new layer */
                filters = this.templateData.enabledFiltersContainer.children().last().find('*[data-js="filterContainer"]');
                clickedButton.closest(this.templateData.filterLayer)
                    .find('*[data-js="filterContainer"]').children().clone(true).appendTo(filters);

                this.model.set('filterLayerCount', filterLayerCount + 1);
                this.updateFallbackHeaders();
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
                var dataLink = dblClickedFilter.attr('data-link');
                var target, source;
                if( dblClickedFilter.closest( this.templateData.availableFilters ).length ) {
                    target = this.templateData.enabledFiltersContainer.children().last().find('*[data-js="filterContainer"]');
                    source = this.templateData.availableFilters;
                } else {
                    source = this.templateData.enabledFiltersContainer.children().last().find('*[data-js="filterContainer"]');
                    target = this.templateData.availableFilters;
                }
                dblClickedFilter.appendTo(target);
                source.find('[data-link="' + dataLink + '"]').appendTo(target);
            },

            removeLayer: function(event) {
                /* 'X' (remove layer) is clicked */ 
                var self = this,
                    layerContainer = $(event.currentTarget).closest('[data-js=filterLayer]');
                
                // make sure we aren't removing a filter that doesn't exist elsewhere:
                _.each(layerContainer.find('[data-js=filterContainer]').children(), function(filter) {
                    var $filter = $(filter);
                    if(this.$el.find('*[data-filter-id="' + $filter.attr('data-filter-id') + '"]').length === 1) {
                        $filter.appendTo(this.templateData.availableFilters);
                    }
                }, this);

                layerContainer.fadeOut(400, function() {
                    var $this = $(this),
                        cache = self.templateData;
                    $this.remove(); // remove from DOM
                    cache.filterLayer = cache.filterLayer.not($this); // remove from cache
                    self.updateFallbackHeaders(); // update interface
                });
                this.model.set('filterLayerCount', this.model.get('filterLayerCount') - 1);
            },

            updateFallbackHeaders: function() {
                /* after a layer addition or removal update labels and buttons */
                var containers = this.templateData.enabledFiltersContainer.children(),
                    maxIndex = containers.length - 1;

                this.templateData.enabledFiltersContainer.find('[data-js=addFallbackBtn]').hide();

                _.each(containers, function(filterLayerContainer, containerIndex) {
                    var $filterLayerContainer = $(filterLayerContainer);

                    if (containerIndex === maxIndex && containerIndex < this.maxIndex) {
                        $filterLayerContainer.find('[data-js=addFallbackBtn]').show();
                    }

                    if (containerIndex === 0) {return;}

                    $filterLayerContainer.find('*[data-target="filterLabel"]').text('Fallback Audience ' + containerIndex);
                    $filterLayerContainer.find('*[data-target="filterLayerFormField"]').attr(
                        'name',
                        'enabled-filters-' + (containerIndex + 1)
                    );
                }, this);
            },

            /* should be in base class, updates campaign name in header if it changes */
            updateName: function() {
                this.templateData.campaignName.text(this.model.get('name'));
            },

            reflectCampaignState: function() {
                /* Add current campaign filter state to UI */
                var campaignFilters = this.campaignModel.get('filters');

                _.each(campaignFilters, function(filterLayer, index) {
                    var nextIndex = index + 1,
                        filter_collection = new FilterCollection(filterLayer, {});

                    _.each(filter_collection.models, function(filter) {
                        var atts = filter.attributes,
                            selector = '*[data-filter-id="set_number=' + atts.feature + '.' + atts.operator + '.' + atts.value + '"]',
                            fromAvailable = this.templateData.availableFilters.find(selector);

                        if (fromAvailable.length) {
                            fromAvailable.dblclick();
                        } else {
                            this.templateData.enabledFiltersContainer
                              .find(selector).clone(true).first().appendTo(this.templateData.availableFilters).dblclick();
                        }
                    }, this);

                    if(nextIndex < campaignFilters.length && campaignFilters[nextIndex].length !== 0) {
                        this._addFallbackLayer();
                        this.templateData.filterContainer.last().empty();
                    }
                }, this);
            },

            showFilterInfo: function() {
                /* shows modal with information regarding how filters work */ 
                modal.update({
                    body: filtersInfoTemplate,
                    longContent: true,
                    title: 'About Audiences'
                });
                modal.templateData.confirmBtn.hide();
                modal.templateData.modalContainer.modal();
            },

            showEmptyFallbackInfo: function() {
                /* shows modal with information regarding how empty fallbacks work */ 
                modal.update( {
                    body: filtersInfoTemplate,
                    title: 'Empty Fallback'
                  } );

                modal.templateData.modalContainer.find('p[data-js="target-audience"]').hide();
                modal.templateData.modalContainer.find('p[data-js="fallback-audience"]').hide();
                modal.templateData.modalContainer.find('span[class="fallback-subtitle"]').hide();
                modal.templateData.confirmBtn.hide();
                modal.templateData.modalContainer.modal();
            },

            /* shows modal with add filter view as content */ 
            showAddFilter: function() {

                modal.update( {
                    body: addFilter.$el,
                    title: 'Add Filter',
                    confirmText: 'Add Filter',
                    showCloseBtn: true
                } );

                modal.templateData.confirmBtn.show();
                modal.templateData.modalContainer.modal();

                addFilter.shown();
            },

            /* Handles the age filter hack (described above) when an age filter is created */
            updateAgeFilterUI: function() {

                var min = this.availableFilters.at( this.availableFilters.length - 2 ).get('min'),
                    max = this.availableFilters.at( this.availableFilters.length - 1 ).get('max'),
                    availableFiltersCount = this.templateData.availableFilters.children().length,
                    combinedAgeFilter = $( filterTemplate( { readable: 'Between ' + min + ' and ' + max } ) );

                combinedAgeFilter.attr('data-link', min + '-' + max);

                _.each( [ availableFiltersCount - 2, availableFiltersCount - 1 ], function( i ) {
                    $( this.templateData.availableFilters.children()[ i ] )
                      .hide()
                      .attr('data-link', min + '-' + max);
                }, this );

                this.templateData.availableFilters.append(combinedAgeFilter);
            },

            /* translates filters into input element value for the backend to handle before
               heading to the next step this format was not done by cbaron, it is not good */
            prepareFormFieldValues: function () {
                var dummyFilterNeglector = "[data-filter-id!='set_number=..']";
                _.each(this.templateData.filterLayer, function(layerContainer, index) {
                    var layerCount = index + 1,
                        $layerContainer = $(layerContainer),
                        $layers = $layerContainer.find('[data-js=filterContainer]').children(dummyFilterNeglector),
                        layerValues = _.map($layers, function(filter) {
                            var filterValue = $(filter).attr('data-filter-id').split('=')[1],
                                escapedValue = filterValue.replace(/"/g, '""');
                            return '"' + escapedValue + '"';
                        }, this);
                    $layerContainer.find('input[name=enabled-filters-' + layerCount + ']').val(layerValues.join(','));
                }, this);
                this.trigger('nextStep');
            },

            /* back is clicked */
            goBack: function() {
                this.trigger('previousStep');
            }

        } );
    }
);
