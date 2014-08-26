/* This was implemented before the redesign and used in the old
   wizard and campaign summary ( why its not a module ).
   filterCollection is a backbone collection of backbone models
   that describe a filter type.  A base model rather than generic defaults
   is probably a better idea */
   
/* At the moment, this code is used to take a json object from the server
   that is a list of campaign filters and generates a filter collection.
   Get readable generates a human readable description for the wizard user,
   parse takes data from the server and applies more naturally named attributes
   to the model, defaults is self documenting code for the most part, on instantiation
   it adds the default attributes, values.  See Backbone documentation for more details. */


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

    /* "url" attribute tells Backbone where to fetch the data,
       "model" returns the appropriate model to be added to the collection */
    filterCollection = Backbone.Collection.extend( {

        url: function() {
            return '/admin/available-filters/' + this.clientId + '/';
        },

        initialize: function( models, options ) {
            return _.extend( this, options );
        },

        model: function( attrs, options ) {
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
