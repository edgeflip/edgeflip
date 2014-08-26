define( [ 'vendor/backbone' ], function( Backbone ) {
    return Backbone.Model.extend( {
        //attributes
        defaults: {
            pk: undefined,
            name: undefined,
            create_dt: undefined,
            description: undefined,
        },
        /* transforms instantiated attributes
           into something more usable */
        parse: function(attrs,options) {
            if( attrs.name && attrs.name.endsWith(" 1") ) {
                attrs.name = attrs.name.substr(0, attrs.name.length-2);
            }
            attrs.create_dt = new Date(attrs.create_dt).toDateString();
            attrs.isPublished = ( attrs.campaignproperties__status === 'published' );
            attrs.name = attrs.root_campaign;

            attrs.thanks_url = attrs.campaign_properties.client_thanks_url;
            attrs.error_url = attrs.campaign_properties.client_error_url;

            attrs.og_type = attrs.fb_obj_attributes.og_type
            attrs.suggested_message_1 = attrs.fb_obj_attributes.msg1_pre + " @name " + attrs.fb_obj_attributes.msg1_post;
            attrs.suggested_message_2 = attrs.fb_obj_attributes.msg2_pre + " @name " + attrs.fb_obj_attributes.msg2_post;

            if( attrs.filters ) {
                attrs.cleaned_filters = []
                for(var filter in attrs.filters) {
                    var cleaned_filter = {}
                    for(var attribute in filter) {
                        cleaned_filter[attribute.feature_type__code].append(attribute)
                    }
                    for(var type_code in cleaned_filter) {
                        attribute = cleaned_filter[type_code]
                        if type_code === "age" {
                        }
                    }
                    cleaned_filters.append(cleaned_filter)
                }
            }
            return attrs;
        }
    } );
} );
