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
            },

            render: function() {

                BaseWidget.prototype.render.call(this)
                    .sizeChart();

                this.xAxis = this.chart.append("g")
                  .attr("class", "x axis")
                  .attr("transform", "translate(0," + this.model.get('graphHeight') + ")")
                  .call(this.model.get('axes').x);

                this.yAxis = this.chart.append("g")
                  .attr("class", "y axis")
                  .attr("x", this.model.get('padding'))
                  .call(this.model.get('axes').y)
                .append("text")
                  .attr("transform", "rotate(-90)")
                  .attr("y", 6)
                  .attr("dy", ".71em")
                  .style("text-anchor", "end")
                  .text( this.model.get('labels').y );

                console.log(this.yAxis.node().getBBox().width);
                console.log(( this.model.get('padding') + this.yAxis.node().getBBox().width ));
                console.log("translate(" + parseInt( this.model.get('padding') + this.yAxis.node().getBBox().width ) + ",0)");
                  
                this.yAxis.attr( "transform",
                    "translate(" + parseInt( this.model.get('padding') + this.yAxis.node().getBBox().width ) + ",0)")

                this.line = this.chart.append("path")
                  .datum( this.model.get('data') )
                  .attr("class", "line")
                  .attr("d", this.model.get('line'));
               
                return this;
            },

            sizeChart: function() {

                BaseWidget.prototype.sizeChart.call(this);

                this.title.attr("y", this.model.get('height') - this.model.get('padding') );

                return this;
            }

        } );
    }
);
