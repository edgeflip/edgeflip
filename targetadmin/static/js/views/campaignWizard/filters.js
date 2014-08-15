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
                'click button[data-js="moreInfoBtn"]': 'showFilterInfo',
                'click span[data-js="emptyFallbackHelpBtn"]': 'showEmptyFallbackInfo',
                'click button[data-js="addFilterBtn"]': 'showAddFilter',
            },

            initialize: function( options ) {

                _.extend( this, options ); 

                this.availableFilters = 
                addFilter.availableFilters = new FilterCollection(
                    [ ], 
                    { clientId: this.model.get('clientId') } 
                ).on( 'add', this.addAvailableFilter, this );

                this.model.on('change:name', this.updateName, this );

                return this.render();
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
 
                    this.templateData.enabledFiltersContainer.append(
                        filterLayerTemplate( {
                            label: 'Target Audience',
                            addBtn: true
                        } ) );
                }
            },

            addAvailableFilter: function(filter) {

                this.templateData.availableFilters.append(
                    filterTemplate( _.extend( {}, filter.toJSON(), { readable: filter.getReadable() } ) )
                );
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

                modal.on( 'confirmed', addFilter.addFilter, addFilter );

                modal.update( {
                    body: addFilter.$el,
                    title: 'Filter Type',
                    confirmText: 'Add Filter',
                    showCloseBtn: true
                } );
                
                modal.templateData.modalContainer.modal();
            },

            triggerNextStep: function() {
                this.trigger('nextStep');
            }

        } );
    }
);
