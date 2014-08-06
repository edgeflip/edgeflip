define( [ 'vendor/backbone', 'vendor/d3' ], function( Backbone, d3 ) {

    return Backbone.Model.extend( {

        defaults: function(options) {
            return {
                data: [ ],
                scale: undefined,
                width: undefined,
                padding: 25,
                title: '',
                titleHeight: 0,
                rowHeight: 15,
                barHeight: 14,
                barOffset: 30,
                labelOffset: 40,
                maxBarWidth: .5, //50% of graph width
            }
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
                height: ( this.get('barHeight') * this.get('data').length ) +
                        this.get('titleHeight') +
                        ( this.get('padding') * 2 )
            } );

        }
    } );
} );
