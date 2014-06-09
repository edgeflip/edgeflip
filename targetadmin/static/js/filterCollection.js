window.filterCollection = Backbone.Collection.extend( {
    model: function( attrs, options ) {
        return ( attrs.feature === 'gender' )
            ? new window.genderFilter( attrs, { parse: true } )
            : ( attrs.feature === 'age' )
                ? new window.ageFilter( attrs, { parse: true } )
                : new window.locationFilter( attrs, { parse: true } )
    }
} );
