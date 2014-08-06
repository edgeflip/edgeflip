define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'views/d3/horizontalBarChart',
      'views/d3/numberBox',
      'templates/insightsWidgets', // function which returns campaign list html
      'css!styles/insightsWidgets' // CSS ( inserted into DOM )
    ],
    function( $, _, Backbone, HorizontalBarChart, NumberBox, template ) {

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
                    el: '#horizontal-bar-chart',
                    title: 'Most Popular Interests',
                    data: [
                        { value: 4, label: 'Veganism' },
                        { value: 8, label: 'Cycling' },
                        { value: 15, label: 'Politics' },
                        { value: 16, label: 'Cynicism' },
                        { value: 23, label: 'Trivia Night' },
                        { value: 42, label: 'The Talking Heads' }
                    ]
                } );

                new NumberBox( {
                    el: '#number-box',
                    title: "It's Numberwang",
                    data: 77
                } );

            }

        } );
    }
);
