define( [ 'vendor/backbone' ], function( Backbone, d3 ) {

    return Backbone.Model.extend( {

        defaults: {
            data: [ ],
            width: undefined,
            height: undefined,
            title: '',
            titleHeight: '',
            padding: 10
        }

    } );
} );
