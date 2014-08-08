define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'vendor/d3',
      'views/d3/widget',
      'models/d3/horizontalBarChart',
      'css!styles/d3/horizontalBarChart' // CSS ( inserted into DOM )
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
                    .createRows();

                return this;
            },

            createRows: function() {

                var self = this;
                
                this.rows = this.chart.selectAll("g")
                    .data(this.model.get('data'))
                    .enter().append("g")
                    .attr("transform", function(d, i) {
                        return "translate(0," +
                            ( ( i * self.model.get('rowHeight') ) +
                               ( self.model.get('padding') * 2 ) +
                               self.model.get('titleHeight')
                            ) + ")"; } );

                this.createValues()
                    .createBars()
                    .createLabels();

                return this;
            },

            createBars: function() {
                
                var self = this;

                this.rows.append("rect")
                    .attr("width", function(data) { return self.model.get('scale')(data.value); })
                    .attr("height", this.model.get('barHeight'))
                    .attr("transform", function(d, i) {
                        return "translate(" + ( 1 * self.model.get('padding') + self.model.get('barOffset') ) + ",0)"; } );

                return this; 
            },

            createValues: function() {
                
                this.rows.append("text")
                    .classed( { 'text': true } )
                    .attr("x", this.model.get('padding') )
                    .attr("y", this.model.get('barHeight') / 2)
                    .text(function(data) { return data.value; });

                return this;
            },

            createLabels: function() {
                
                this.rows.append("text")
                    .classed( { 'text': true } )
                    .attr("x", this.model.get('padding') +
                               ( this.model.get('width') * this.model.get('maxBarWidth') ) +
                               this.model.get('labelOffset'))
                    .attr("y", this.model.get('barHeight') / 2)
                    .text(function(data) { return data.label; });

                return this;
            }

        } );
    }
);
