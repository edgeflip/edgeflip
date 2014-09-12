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


    var readable_list = function(list, set_operator) {
        var first_part = list.slice(0, -2),
            last_two = list.slice(-2),
            full_string = [first_part.join(", "), last_two.join(" " + set_operator + " ")].filter(function(e) { return e; }).join(", ");
        return full_string;
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
            return 'Lives in ' + readable_list(this.get('values'), 'or');
        }
    });

    var interestFilter = Backbone.Model.extend({
        defaults: {
            topic: undefined
        },
        _expr: /topics\[(.+)\]/,
        parse: function (attrs) {
            var groups = attrs.feature.match(this._expr);
            return {
                feature: 'interest',
                operator: 'eq',
                value: groups[1],
            };
        },
        getReadable: function() {
            return 'Interest in ' + this.get('value');
        }
    });

    /* "url" attribute tells Backbone where to fetch the data,
       "model" returns the appropriate model to be added to the collection */
    filterCollection = Backbone.Collection.extend( {

        url: function() {
            return '/admin/client/' + this.clientId + '/filters.json';
        },

        initialize: function( models, options ) {
            return _.extend( this, options );
        },

        readable_list: readable_list,

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
