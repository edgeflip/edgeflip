define( [ 'jquery', 'ourBackbone', 'models/filter' ], function( $, Backbone, filter ) {
    return Backbone.Collection.extend( {
        model: filter
    } );
} );
