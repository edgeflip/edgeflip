( function($) {
    window.campaignWizardFilterView = Backbone.View.extend( {

        emptyFallbackHelpText: "We recommend selecting the 'empty fallback' feature in case some of your supporters have few friends in your Target and Fallback Audiences. When the empty fallback feature is selected, the Targeted Sharing application will still suggest the friends most likely to support your organization, even though no filters are enabled. The 'empty fallback' feature is selected by default for new campaigns.",

        events: {
            'click [data-js="learnMoreBtn"]': 'learnMoreClicked',
            'click [data-js="addLayerBtn"]': 'addLayerClicked',
            'click [data-js="removeLayerBtn"]': 'removeLayerClicked',
            'dblclick .draggable': 'filterDblClicked',
            'click [data-js="previousBtn"]': 'previousClicked',
            'click [data-js="nextBtn"]': 'nextClicked'
        },

        initialize: function( options ) {

            _.extend( this, options );

            this.model = new Backbone.Model( {
                layerCount: 1
            } );

            this.slurpHtml();

            this.insertExistingFilters();

            _.each( [ 'existingFilters', 'enabledFilters' ], function( elRef ) {
                this.templateData[ elRef ].sortable( {
                    connectWith: ".target-well",
                    receive: this.filterReceived
                } ) }, this );

            $( ".sortable" ).disableSelection();

            this.templateData.emptyFallbackHelpText.append( this.emptyFallbackHelpText );
            this.templateData.emptyFallbackHelpIcon.data( 'content', this.emptyFallbackHelpText );
        },

        learnMoreClicked: function() {
            $('#target-audience-help-modal').modal();
        },

        filterTemplate: function( data ) {
            return '<div title="' + data.readable + '" data-filter-id="set_number=' + [ data.feature, data.operator, data.value ].join('.') + '" class="span2 draggable">' +
                '<div class="filter-content-container"><span class="filter">' + data.readable + '</span></div></div>';
        },

        layerTemplate: function( data ) {
            return '<section data-js="layerContainer" class="span12" data-layer="' + data.layerCount + '">' +
            '<div class="row"><div class="span11"><h6 class="layer-text-header pull-left"><span data-js="layerHeading">Fallback Audience ' + (data.layerCount - 1) + '</span></h6></div>' +
            '<div class="span1"><h6 data-js="removeLayerBtn" data-layer="' + data.layerCount + '" class="btn btn-link pull-right remove-layer">' +
            '<i class="icon-remove"></i></h6></div></div><input data-js="layerInput" type="hidden" id="id_enabled-filters-' + 
            data.layerCount + '" name="enabled-filters-' + data.layerCount + 
            '"><div data-js="enabledFilters" class="clearfix well sortable target-well filter-well" id="enabled-filters-' + 
            data.layerCount + '">' + data.previousLayerHtml  + '</div></section>';
        },

        insertExistingFilters: function() {
            this.filters.each( function( filter ) {
                this.templateData.existingFilters.append(
                    this.filterTemplate(
                        _.extend( filter.attributes, { readable: filter.getReadable() } ) ) );
            }, this );
        },

        addLayerClicked: function() {
            this.model.set( 'layerCount', this.model.get('layerCount') + 1 );

            this.slurpHtml( {
                template: this.layerTemplate( {
                    layerCount: this.model.get('layerCount'),
                    previousLayerHtml: this.templateData.enabledFilters.last().html()
                } ),
                insertion: { $el: this.templateData.enabledFiltersContainer, method: 'append' }
            } );

            this.templateData.enabledFiltersContainer.children('section').last().find('h6').first().append( this.templateData.addLayerBtn );

            this.templateData.enabledFilters.last().sortable( { connectWith: ".target-well" } );
            
            if( this.model.get( 'layerCount' ) === 4 ) {
                this.templateData.addLayerBtn.prop( 'disabled', true );
            }
        },

        removeLayerClicked: function(e) {
            var self = this;

            this.model.set( 'layerCount', this.model.get('layerCount') - 1 );

            this.removeLayer( $( e.target ).closest('[data-js="layerContainer"]') );

            if( this.templateData.addLayerBtn.prop( 'disabled' ) ) {
                this.templateData.addLayerBtn.prop( 'disabled', false );
            }
        },

        removeLayer: function( el ) {
            var self = this;

            el.fadeOut( 400, function() {
                if( el.find('[data-js="addLayerBtn"]').length ) {
                    $( self.$el.find('[data-js="layerContainer"]')[ self.model.get('layerCount') - 1 ] )
                        .find('h6').first().append( self.templateData.addLayerBtn );
                }
                _.each( el.find('.draggable'), function( filter ) {
                    var filterId = $(filter).attr('data-filter-id');
                    if( this.templateData.existingFilters.find( '[data-filter-id="' + filterId + '"]' ).length === 0 &&
                        $('#enabled-filters-1').find( 'div[data-filter-id="' + filterId + '"]' ).length === 0 ) {

                        this.templateData.existingFilters.append( filter );
                    }
                }, self );

                el.empty().remove();
                self.updateLayerNumbers();
            } );
        },

        updateLayerNumbers: function() {
            
            this.$el.find('[data-js="layerHeading"]').each( function( i, el ) {
                $(el).text( 'Fallback Audience ' + ( i + 1 ) ) } );
            
            this.$el.find('[data-js="layerInput"]').each( function( i, el ) {
                $(el).attr( 'name', 'id_enabled-filters-' + ( i + 1 ) ) } );
        },

        filterReceived: function( event, ui ) {
            var dataLink = ui.item.attr('data-link');
            if( dataLink ) {
                ui.sender.find('[data-link="' + dataLink + '"]').appendTo( $(event.target) );
            }
        },

        filterDblClicked: function( e ) {
            var clickedEl = $(e.currentTarget),
                dataLink = clickedEl.attr('data-link'),
                lastEnabled = this.templateData.enabledFilters.last(),
                availableFilters = this.templateData.existingFilters;

            if( clickedEl.parent().attr('data-js') === 'existingFilters' ) {
                if( dataLink ) {
                    clickedEl.siblings('[data-link="' + dataLink + '"]').appendTo( lastEnabled );
                }
                lastEnabled.append( clickedEl );
            } else {
                if( dataLink ) {
                    clickedEl.siblings('[data-link="' + dataLink + '"]').appendTo( availableFilters );
                }
                clickedEl.appendTo( availableFilters );
            }
        },

        previousClicked: function() {
            window.campaignWizardIntro.cycleCarousel();
        },

        nextClicked: function() {

            _.each( this.templateData.layerContainer, function( layer ) {
                var $layer = $(layer);
                $( $layer.find('[data-js="layerInput"]') ).val(
                    _.map( $layer.find('[data-js="enabledFilters"]').children(), function( filter ) {
                        return '"' + $(filter).attr('data-filter-id').split('=')[1] + '"'
                    }, this ) );
            }, this );
        }
    } );

} )(jQuery);
