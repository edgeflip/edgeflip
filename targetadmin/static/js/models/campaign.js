define( [ 'jquery', 'vendor/underscore', 'vendor/backbone' ], function( $, _, Backbone ) {
    return Backbone.Model.extend( {
        defaults: {
            pk: undefined,
            name: undefined,
            create_dt: undefined
        },
        parse: function(attrs,options) {
            console.log(attrs);
            if( attrs.name && attrs.name.endsWith(" 1") ) {
                attrs.name = attrs.name.substr(0, attrs.name.length-2);
            }

            attrs.create_dt = new Date(attrs.create_dt).toDateString();
            return attrs;
        }
    } );
} );
