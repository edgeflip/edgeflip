define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'vendor/d3',
      'models/d3/horizontalBarChart',
      'css!styles/horizontalBarChart' // CSS ( inserted into DOM )
    ],
    function( $, _, Backbone, d3, Model, template ) {

        return Backbone.View.extend( {
            
            initialize: function( options ) {

                var self = this;

                _.extend( this, options ); 

                this.model = new Model( {
                    data: this.data,
                    title: this.title,
                    width: this.$el.width()
                } );

                this.model.on( "change:height", this.sizeChart, this );

                return this.render();
            },

            render: function() {
                
                $('<svg class="chart"></svg>').appendTo( this.$el );
                
                this.chart = d3.select(".chart");

                this.createTitle()
                    .createRows();

                return this;
            },

            sizeChart: function() {

                this.chart.attr("width", this.model.get('width'))
                          .attr("height", this.model.get('height'));

                this.$el.height( this.model.get('height') );

                return this;
            },

            createTitle: function() {

                this.title = 
                    this.chart.append("text")
                        .classed( { 'title': true } )
                        .attr("x", this.model.get('padding') )
                        .attr("y", this.model.get('padding') )
                        .attr("dy", ".35em" )
                        .text( this.model.get('title') );
                               
                this.model.set("titleHeight", this.title.node().getBBox().height);

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
                               self.model.get('padding') +
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
                
                var self = this;

                this.rows.append("text")
                    .attr("x", this.model.get('padding') )
                    .attr("y", this.model.get('barHeight') / 2)
                    .attr("dy", ".35em")
                    .text(function(data) { return data.value; });

                return this;
            },

            createLabels: function() {
                
                var self = this;

                this.rows.append("text")
                    .attr("x", this.model.get('padding') +
                               ( this.model.get('width') * this.model.get('maxBarWidth') ) +
                               this.model.get('labelOffset'))
                    .attr("y", this.model.get('barHeight') / 2)
                    .attr("dy", ".35em")
                    .text(function(data) { return data.label; });

                return this;
            }

        } );
    }
);
