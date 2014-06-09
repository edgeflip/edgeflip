window.campaignFilter = Backbone.Model.extend( {
    defaults: {
        feature: undefined,
        operator: undefined,
        value: undefined
    }
} );

window.genderFilter = Backbone.Model.extend( {

    defaults: function() {
        return _.extend(
            { gender: undefined },
            window.campaignFilter.prototype.defaults );
    },

    parse: function( attrs ) {
        return _.extend( { gender: attrs.value }, attrs );
    },

    getReadable: function() { return this.get('gender') + 's'; }

} );

window.ageFilter = Backbone.Model.extend( {

    defaults: function() {
        return _.extend(
            { min: undefined, max: undefined },
            window.campaignFilter.prototype.defaults );
    },

    parse: function( attrs ) {
        var rv = { };
        rv[ attrs.operator ] = attrs.value;
        return _.extend( rv, attrs );
    },

    getReadable: function() {
        return this.has('min')
            ? this.get('min') + ' and older'
            : this.get('max') + ' and younger';
    }

} );

window.locationFilter = Backbone.Model.extend( {
    defaults: function() {
        return _.extend(
            { type: undefined, values: [ ] },
            window.campaignFilter.prototype.defaults );
    },

    parse: function( attrs ) {
        return _.extend(
            { type: attrs.feature, values: attrs.value.split('||') },
            attrs );
    },

    getReadable: function() {

        return 'Lives in ' + ( ( this.get('values').length < 2 )
            ? this.get('values')
            : this.get('values').join(' or ') );
    }
} );
