define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'vendor/d3',
      'css!styles/d3/widget' // CSS ( inserted into DOM )
    ],
    function( $, _, Backbone ) {

        return Backbone.View.extend( {
            
            initialize: function( options, Model ) {

                _.extend( this, options ); 

                this.model = new Model( {
                    data: this.data,
                    title: this.title,
                    width: ( this.width || this.$el.width() )
                } ).on( "change:height", this.sizeChart, this );

                return this;
            },

            render: function() {
                
                this.chart = d3.select( $('<svg class="d3-chart"></svg>').appendTo( this.$el ).get(0) );

                if( this.model.get('title') ) { this.createTitle(); }
                
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
                        .text( this.model.get('title') );
                               
                this.model.set("titleHeight", this.title.node().getBBox().height);

                this.title.attr( "y", this.model.get('padding') + this.model.get('titleHeight') );

                return this;
            }

        } );
    }
);
