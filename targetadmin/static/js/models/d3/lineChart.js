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
                        spacing: 25,
                        graphHeight: 500,
                        scale: { x: undefined, y: undefined },
                        axes: { x: undefined, y: undefined },
                        metaData: { x: undefined, y: undefined },
                        line: undefined
                    }
                );
            },

            initialize: function(options) {

                var attrs = {
                    scale: this.get('scale'),
                    line: this.get('line'),
                    axes: this.get('axes'),
                    metaData: this.get('metaData')
                 };

                this.on( "change:titleHeight", this.calculateHeight, this );
                this.on( "change:scale", this.updateAxes );
              
                if( attrs.scale.x === undefined || attrs.scale.y === undefined ) { 
                    
                    _.each( [ { axis: 'x', attr: 'width' },
                              { axis: 'y', attr: 'graphHeight' } ], function(data) {

                        if( attrs.metaData[data.axis] && attrs.metaData[data.axis].type === 'time' ) {
                            attrs.scale[data.axis] = d3.time.scale().range([0, this.get(data.attr)])
                        } else {
                            attrs.scale[data.axis] = d3.scale.linear().range([0, this.get(data.attr)])
                        }
                    }, this );

                    this.set( 'scale', attrs.scale );
                }
                
                if( attrs.axes.x === undefined || attrs.axes.y === undefined ) { 
                    
                    this.set( 'axes', {
                        x: d3.svg.axis()
                            .scale( attrs.scale.x )
                            .orient("bottom"),
                        y: d3.svg.axis()
                            .scale( attrs.scale.y )
                            .orient("left")
                    } );
                }
                
                if( attrs.line === undefined ) {

                    this.set( 'line',
                        d3.svg.line().x(function(d) { return attrs.scale.x(d[0]); })
                                     .y(function(d) { return attrs.scale.y(d[1]); }) );
                 }

                if( ( attrs.metaData.x && attrs.metaData.x.parse ) ||
                    ( attrs.metaData.y && attrs.metadata.y.parse ) ) {

                    //Lou Reed, not michael bay
                    var transformer = _.map( [ 'x', 'y' ], function( axis ) {
                        return ( attrs.metaData[axis] && attrs.metaData[axis].parse )
                            ? attrs.metaData[axis].parse
                            : function(d) { return d; }
                    }, this );

                    var transformedData = _.map( this.get('data'), function( row ) {
                        return _.map( [ 0, 1 ], function( index ) {
                            return transformer[index]( row[index] );
                        } );
                    } );

                    this.set( 'data', transformedData );
                
                    attrs.scale.x.domain( d3.extent( transformedData, function(d) { return d[0]; }));
                    attrs.scale.y.domain( d3.extent( transformedData, function(d) { return d[1]; }));
                }
                
                return this;
            },

            calculateHeight: function() {

                this.set( {
                    height: this.get('titleHeight') +
                            this.get('spacing') +
                            this.get('graphHeight') +
                            ( this.get('padding') * 2 )
                } );
            }
        } );
    }
);
