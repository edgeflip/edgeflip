define( [ 'ourBackbone' ], function( Backbone ) {
    return Backbone.Model.extend( {
        defaults: {
            "feature": undefined,
            "operator": undefined,
            "value": undefined
        }
    } );
} );
