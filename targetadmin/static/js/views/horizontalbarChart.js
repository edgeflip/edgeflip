define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'vendor/d3',
      'models/d3/horizontalBarChart',
      'css!styles/horizontal-bar-chart' // CSS ( inserted into DOM )
    ],
    function( $, _, Backbone, d3, template ) {

        return Backbone.View.extend( {
            
            events: {
            },

            initialize: function( options ) {

                _.extend( this, options ); 

                return this.render();
            },

            render: function() {

                $('<svg class="chart"></svg>').appendTo( this.$el );

                return this;
            }

        } );
    }
);
