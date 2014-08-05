define( [ 'vendor/backbone', 'vendor/d3' ], function( Backbone, d3 ) {

    return Backbone.Model.extend( {

        defaults: function(options) {
            return {
                data: [ ],
                scale: undefined,
                width: '',
                title: '',
                barHeight: 15,
                maxBarWidth: .5, //50% of graph width
                padding: 25
            }
        },

        initialize: function(options) {

            if( ! this.has('scale') ) {
                this.set( {
                    scale: d3.scale.linear()
                                .domain([0, d3.max(this.get('data'), function(d) { return d.value; })])
                                .range([0, this.get('width') * this.get('maxBarWidth') ])
                } );
            }

            this.set( {
                height: ( this.get('barHeight') * this.get('data').length ) +
                        ( this.get('padding') * 2 )
            } );

            return this;
        }
    } );
} );
