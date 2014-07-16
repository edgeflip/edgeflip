define( [ 'jquery', 'vendor/underscore', 'vendor/backbone' ], function( $, _, Backbone ) {
    return Backbone.Model.extend( {
        defaults: {
            pk: undefined,
            name: undefined,
            create_dt: undefined
        },
        parse: function(response,options) {
            if( response.name.endsWith(" 1") ) {
                response.name = response.name.substr(0, response.name.length-2);
            }

            response.create_dt = new Date(response.create_dt).toDateString();
            return response;
        }
    } );
} );
