define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'vendor/d3',
      'views/d3/widget',
      'models/d3/numberBox',
      'css!styles/d3/numberBox' // CSS ( inserted into DOM )
    ],
    function( $, _, Backbone, d3, BaseWidget, Model ) {

        return BaseWidget.extend( {
            
            initialize: function( options ) {

                BaseWidget.prototype.initialize.apply(
                    this, [ options, Model ] );

                return this.render();
            },

            render: function() {

                BaseWidget.prototype.render.call(this)
                    .createColumns();
               
                return this;
            },

            sizeChart: function() {

                BaseWidget.prototype.sizeChart.call(this);

                this.labels.attr("y", this.model.get('height') - this.model.get('padding') );

                return this;
            },

            createColumns: function() {

                var self = this;

                this.columnWidth = this.model.get('width') /
                                   this.model.get('data').length;

                this.columns = this.chart.selectAll("g")
                    .data(this.model.get('data'))
                    .enter().append("g")
                    .attr("transform", function(d, i) {
                        return "translate(" + ( i * self.columnWidth ) + ",0)";
                     } );

                this.createNumbers()
                    .createLabels();

                return this;
            },

            createNumbers: function() {

                this.numbers = 
                    this.columns.append("text")
                        .classed( { 'number': true } )
                        .attr("x", this.columnWidth / 2 )
                        .text(function(data) { return data.number; });

                this.model.set("numberHeight", this.numbers.node().getBBox().height);
                
                this.numbers.attr("y", this.model.get('padding') + this.model.get('numberHeight') );

                return this;
            },

            createLabels: function() {

                this.labels = 
                    this.columns.append("text")
                        .classed( { 'number-label': true } )
                        .attr("x", this.columnWidth / 2)
                        .text(function(data) { return data.label; });

                this.model.set("labelHeight", this.labels.node().getBBox().height);
                
                return this;
            }

        } );
    }
);
