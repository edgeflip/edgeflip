define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'models/filterModels'
    ],
    function( $, _, Backbone, filterCollection ) {
        return Backbone.Model.extend( {
            defaults: {
                pk: undefined,
                name: undefined,
                create_dt: undefined
            },
            parse: function(attrs,options) {
                var rv = { };

                if( attrs.name && attrs.name.endsWith(" 1") ) {
                    rv.name = attrs.name.substr(0, attrs.name.length-2);
                }

                rv.create_dt = new Date(attrs.create_dt).toDateString();
    
                rv.filters = new filterCollection( attrs.filters, { parse: true } );
                rv.fbObjAttributes = attrs.fb_obj_attributes;
                rv.properties = attrs.properties;
                rv.pk = attrs.pk;

                return rv;
            }
        } );
} );
