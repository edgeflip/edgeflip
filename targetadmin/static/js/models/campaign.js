var nicely_formatted_list = function(list) {
    first_part = list.slice(0, -2);
    last_two = list.slice(-2);
    full_string = [first_part.join(", "), last_two.join(", or ")].filter(function(e) { return e; }).join(", ");
    return full_string;
};

define( [ 'vendor/backbone' ], function( Backbone ) {
    return Backbone.Model.extend( {
        //attributes
        defaults: {
            pk: undefined,
            name: undefined,
            create_dt: undefined,
            description: undefined,
        },
        format: function(type_code, attribute_list) {
            if( type_code === "age" ) {
                if(attribute_list.length == 1) {
                    var base_message = attribute_list[0].value + " years old or "
                    var suffix = attribute_list[0].operator === "max" ? "younger" : "older";
                    var full_message = base_message + suffix;
                    return full_message;
                } else {
                    var winning_min = 0;
                    var winning_max = 999;
                    for(var index in attribute_list) {
                        if( attribute_list[index].operator === "max" ) {
                            if( attribute_list[index].value < winning_max ) {
                                winning_max = attribute_list[index].value
                            }
                        }
                        if( attribute_list[index].operator === "min" ) {
                            if( attribute_list[index].value > winning_min ) {
                                winning_min = attribute_list[index].value
                            }
                        }
                    }
                    return "Between " + winning_min + " and " + winning_max + " years old"
                }
            } else if( type_code === "state" || type_code === "city" || type_code === "full_location") {
                var base_message = "Lives in ";
                var locales = attribute_list.map(function(attribute) {
                    var locale_string;
                    if( attribute.operator === "in" ) {
                        locale_string = nicely_formatted_list(attribute.value.split("||"));
                    }
                    else {
                        locale_string = attribute.value;
                    }
                    return base_message + locale_string;
                });
                return nicely_formatted_list(locales);
            } else if( type_code === "topics" ) {
                var topics = attribute_list.map(function(attribute) {
                    return attribute.value;
                });
                return "Interested in" + nicely_formatted_list(topics);
            }
        },
        parse: function(attrs,options) {
            if( attrs.name && attrs.name.endsWith(" 1") ) {
                attrs.name = attrs.name.substr(0, attrs.name.length-2);
            }
            attrs.create_dt = new Date(attrs.create_dt).toDateString();
            attrs.isPublished = ( attrs.campaignproperties__status === 'published' );

            if( attrs.root_campaign ) {
                attrs.name = attrs.root_campaign;
            }

            if( attrs.campaign_properties ) {
                attrs.thanks_url = attrs.campaign_properties.client_thanks_url;
                attrs.error_url = attrs.campaign_properties.client_error_url;
            }

            if( attrs.fb_obj_attributes ) {
                attrs.og_type = attrs.fb_obj_attributes.og_type;
                attrs.headline = attrs.fb_obj_attributes.sharing_prompt;
                attrs.subheader = attrs.fb_obj_attributes.sharing_sub_header;
                attrs.suggested_message_1 = attrs.fb_obj_attributes.msg1_pre + " @name " + attrs.fb_obj_attributes.msg1_post;
                attrs.suggested_message_2 = attrs.fb_obj_attributes.msg2_pre + " @name " + attrs.fb_obj_attributes.msg2_post;
                attrs.og_title = attrs.fb_obj_attributes.og_title;
                attrs.og_image = attrs.fb_obj_attributes.og_image;
                attrs.og_text = attrs.fb_obj_attributes.og_text;
            }

            if( attrs.filters ) {
                attrs.empty_fallback = false;
                attrs.cleaned_filters = []
                for(var filter_index in attrs.filters) {
                    var cleaned_filter = {}
                    var filter = attrs.filters[filter_index];
                    for(var stuff_index in filter) {
                        var stuff = filter[stuff_index];
                        for(var att_index in stuff) {
                            var attribute = stuff[att_index];
                            if(!(attribute.feature_type__code in cleaned_filter)) {
                                cleaned_filter[attribute.feature_type__code] = []
                            }
                            cleaned_filter[attribute.feature_type__code].push(attribute)
                        }
                    }
                    for(var type_code in cleaned_filter) {
                        cleaned_filter[type_code] = this.format(type_code, cleaned_filter[type_code])
                    }
                    if(
                        (filter_index == attrs.filters.length - 1) &&
                        (filter[0].length == 0)
                    ) {
                        attrs.empty_fallback = true;
                    } else {
                        attrs.cleaned_filters.push(cleaned_filter)
                    }
                }
            }
            if( attrs.content ) {
                attrs.content_url = attrs.content_url;
            }
            return attrs;
        }
    } );
} );
