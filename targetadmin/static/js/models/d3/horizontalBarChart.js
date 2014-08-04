define( [ 'vendor/backbone' ], function( Backbone ) {

    return Backbone.Model.extend( {

        defaults: {
            data: [ ],
            width: '100%',
            barHeight: 20
        },

        parse: function(attrs,options) {
            if( attrs.name && attrs.name.endsWith(" 1") ) {
                attrs.name = attrs.name.substr(0, attrs.name.length-2);
            }

            attrs.create_dt = new Date(attrs.create_dt).toDateString();
            attrs.isPublished = ( attrs.campaignproperties__status === 'published' )
            return attrs;
        }
    } );
} );
