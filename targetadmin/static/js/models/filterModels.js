var filterCollection;

( function( $ ) {

    var genericDefaults = {
        feature: undefined,
        operator: undefined,
        value: undefined
    }

    var genderFilter = Backbone.Model.extend( {

        defaults: function() {
            return _.extend(
                { gender: undefined },
                genericDefaults );
        },

        parse: function( attrs ) {
            return _.extend(
                { gender: attrs.value },
                attrs );
        },

        getReadable: function() { return this.get('gender') + 's'; }

    } );

    var ageFilter = Backbone.Model.extend( {
        defaults: function() {
            return _.extend(
                { min: undefined,
                  max: undefined },
                genericDefaults );
        },

        parse: function( attrs ) {
            //Hurry ECMA 6
            //http://wiki.ecmascript.org/doku.php?id=harmony%3aobject_literals#object_literal_computed_property_keys
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

    var locationFilter = Backbone.Model.extend( {
        defaults: function() {
            return _.extend(
                { type: undefined,
                  values: [ ] },
                genericDefaults );
        },

        parse: function( attrs ) {
            return _.extend(
                { type: attrs.feature,
                  values: attrs.value.split('||') },
                attrs );
        },

        getReadable: function() {

            return 'Lives in ' + ( ( this.get('values').length < 2 )
                ? this.get('values')
                : this.get('values').join(', ') );
        }
    } );

    var interestFilter = Backbone.Model.extend({
        defaults: {
            topic: undefined
        },
        _expr: /topics\[(.+)\]/,
        parse: function (attrs) {
            var groups = attrs.feature.match(this._expr);
            return {
                topic: groups[1]
            };
        },
        getReadable: function() {
            return 'Interest in ' + this.get('topic');
        }
    });

    filterCollection = Backbone.Collection.extend( {
        model: function( attrs, options ) {
            console.log(attrs);
            switch (attrs.feature_type__code) {
                case 'gender':
                    return new genderFilter( attrs, { parse: true } );
                case 'age':
                    return new ageFilter( attrs, { parse: true } );
                case 'full_location':
                case 'state':
                case 'city':
                    return new locationFilter( attrs, { parse: true } );
                case 'topics':
                    return new interestFilter(attrs, {parse: true});
            }
            throw "unrecognized feature type: " + attrs.feature_type__code;
        }
    } );

})(jQuery);
