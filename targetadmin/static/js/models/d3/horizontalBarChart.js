define(
    [
      'vendor/backbone',
      'vendor/underscore',
      'vendor/d3',
      'models/d3/widget'
    ],
    function( Backbone, _, d3, BaseModel ) {

        return BaseModel.extend( {

            defaults: function(options) {
                return _.extend(
                    {},
                    BaseModel.prototype.defaults,
                    {
                        scale: undefined,
                        rowHeight: 15,
                        barHeight: 14,
                        barOffset: 30,
                        labelOffset: 40,
                        maxBarWidth: .5, //50% of graph width
                    }
                );
            },

            initialize: function(options) {

                this.on( "change:titleHeight", this.calculateHeight, this );

                if( ! this.has('scale') ) {
                    this.set( {
                        scale: d3.scale.linear()
                                    .domain([0, d3.max(this.get('data'), function(d) { return d.value; })])
                                    .range([0, this.get('width') * this.get('maxBarWidth') ])
                    } );
                }

                return this;
            },

            calculateHeight: function() {
                this.set( {
                    height: ( this.get('rowHeight') * this.get('data').length ) +
                            this.get('titleHeight') +
                            ( this.get('padding') * 3 ) //spacing between header and first row is padding
                } );

            }
        } );
    }
);
