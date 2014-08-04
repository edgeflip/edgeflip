define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'views/d3/horizontalBarChart',
      'templates/insightsWidgets', // function which returns campaign list html
      'css!styles/insightsWidgets' // CSS ( inserted into DOM )
    ],
    function( $, _, Backbone, HorizontalBarChart, template ) {

        return Backbone.View.extend( {
            
            events: {
            },

            initialize: function( options ) {

                _.extend( this, options ); 

                return this.render();
            },

            render: function() {

                this.slurpHtml( {
                    template: template(),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                this.postRender();

                return this;
            },

            postRender: function() {

                new HorizontalBarChart( {
                    el: '#horizontal-bar-chart'
                } );
            }

        } );
    }
);
