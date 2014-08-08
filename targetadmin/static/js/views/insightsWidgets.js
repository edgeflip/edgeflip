define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'vendor/d3',
      'views/d3/horizontalBarChart',
      'views/d3/numberBox',
      'views/d3/lineChart',
      'fakeData/lineChart',
      'templates/insightsWidgets', // function which returns campaign list html
      'css!styles/insightsWidgets' // CSS ( inserted into DOM )
    ],
    function( $, _, Backbone, d3, HorizontalBarChart, NumberBox, LineChart, lineChartData, template ) {

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
                    data: [ { label: "It's Numberwang", number: 77 } ]
                } );

                new NumberBox( {
                    el: '#gender-box',
                    data: [
                        { label: 'Females', number: 51 },
                        { label: 'Males', number: 49 }
                    ]
                } );

                new LineChart( { 
                    el: '#line-chart',
                    data: lineChartData,
                    labels: { x: 'Date', y: 'Price' },
                    metaData: {
                        x: {
                            type: 'time',
                            parse: d3.time.format("%d-%b-%y").parse,
                        }
                    },
                    graphHeight: 500,
                } );

            }

        } );
    }
);
