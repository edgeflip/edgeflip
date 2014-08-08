define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'vendor/d3',
      'views/d3/widget',
      'models/d3/lineChart',
      'css!styles/d3/lineChart' // CSS ( inserted into DOM )
    ],
    function( $, _, Backbone, d3, BaseWidget, Model ) {

        return BaseWidget.extend( {
            
            initialize: function( options ) {

                BaseWidget.prototype.initialize.apply(
                    this, [ options, Model ] );

                return this.render();
                
                x.domain(d3.extent(options.data.rows, function(d) { return d[0]; }));
                y.domain(d3.extent(options.data.rows, function(d) { return d[1]; }));

                svg.append("g")
                  .attr("class", "x axis")
                  .attr("transform", "translate(0," + height + ")")
                  .call(xAxis);

                svg.append("g")
                  .attr("class", "y axis")
                  .call(yAxis)
                .append("text")
                  .attr("transform", "rotate(-90)")
                  .attr("y", 6)
                  .attr("dy", ".71em")
                  .style("text-anchor", "end")
                  .text("Price ($)");
              

                svg.append("path")
                  .datum(options.data.rows)
                  .attr("class", "line")
                  .attr("d", line);
            },

            render: function() {

                BaseWidget.prototype.render.call(this)
                    .sizeChart();

                this.chart.append("g");
               
                return this;
            },

            /*
            sizeChart: function() {

                BaseWidget.prototype.sizeChart.call(this);

                this.labels.attr("y", this.model.get('height') - this.model.get('padding') );

                return this;
            },
            */

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
