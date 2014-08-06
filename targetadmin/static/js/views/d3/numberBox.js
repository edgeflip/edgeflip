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
                    .createNumber();
               
                return this;
            },

            sizeChart: function() {

                BaseWidget.prototype.sizeChart.call(this);

                this.title.attr("y", this.model.get('height') - this.model.get('padding') );

                return this;
            },

            createNumber: function() {

                this.number =
                    this.chart.append("text")
                        .classed( { 'number': true } )
                        .attr("x", this.model.get('width') / 2 )
                        .text( this.model.get('data') );

                this.model.set("numberHeight", this.number.node().getBBox().height);
                        
                this.number.attr("y", this.model.get('padding') + this.model.get('numberHeight') );

                return this;
            }

        } );
    }
);
