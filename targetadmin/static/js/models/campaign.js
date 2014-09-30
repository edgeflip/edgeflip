define([
    'vendor/backbone',
    'models/filters',
], function(Backbone, FilterCollection) {
    var readable_list = function(list, set_operator) {
        // TODO: DRY up this incarnation and the one in the filter model
        var first_part = list.slice(0, -2),
            last_two = list.slice(-2),
            combined = [first_part.join(", "), last_two.join(" " + set_operator + " ")];
        return combined.filter(function(el) {return el;}).join(", ");
    };

    return Backbone.Model.extend( {
        //attributes
        defaults: {
            pk: undefined,
            name: undefined,
            create_dt: undefined,
            description: undefined,
        },
        format: function(type_code, model_list) {
            if( type_code === "age" ) {
                if(model_list.length == 1) {
                    return model_list[0].getReadable();
                } else {
                    var winning_min = 0;
                    var winning_max = 999;
                    for(var index in model_list) {
                        var atts = model_list[index].attributes;
                        if( atts.operator === "max" ) {
                            if( atts.value < winning_max ) {
                                winning_max = atts.value
                            }
                        }
                        if( atts.operator === "min" ) {
                            if( atts.value > winning_min ) {
                                winning_min = atts.value
                            }
                        }
                    }
                    return "Between " + winning_min + " and " + winning_max + " years old"
                }
            } else if( type_code === "interest" ) {
                var topics = model_list.map(function(model) {
                    return model.attributes.value;
                });
                return "Interested in " + readable_list(topics, 'and');
            } else {
                var values = model_list.map(function(model) {
                    return model.getReadable();
                });
                return readable_list(values, 'and');
            }
        },
        parse: function(attrs, options) {
            if (attrs.name && attrs.name.endsWith(" 1")) {
                attrs.name = attrs.name.substr(0, attrs.name.length-2);
            }
            attrs.create_dt = new Date(attrs.create_dt).toDateString();
            attrs.isPublished = attrs.campaignproperties__status === 'published';

            if (attrs.campaign_properties) {
                attrs.thanks_url = attrs.campaign_properties.client_thanks_url;
                attrs.error_url = attrs.campaign_properties.client_error_url;
            }

            if (attrs.fb_obj_attributes) {
                attrs.org_name = attrs.fb_obj_attributes.org_name;
                attrs.headline = attrs.fb_obj_attributes.sharing_prompt;
                attrs.subheader = attrs.fb_obj_attributes.sharing_sub_header;
                attrs.suggested_message_1 = attrs.fb_obj_attributes.msg1_pre + " @name " + attrs.fb_obj_attributes.msg1_post;
                attrs.suggested_message_2 = attrs.fb_obj_attributes.msg2_pre + " @name " + attrs.fb_obj_attributes.msg2_post;
                attrs.og_title = attrs.fb_obj_attributes.og_title;
                attrs.og_image = attrs.fb_obj_attributes.og_image;
                attrs.og_description = attrs.fb_obj_attributes.og_description;
            }

            if (attrs.filters) {
                attrs.empty_fallback = false;
                attrs.cleaned_filters = []
                for(var layer_index in attrs.filters) {
                    var cleaned_filter = {}
                    var layer = attrs.filters[layer_index];
                    for(var stuff_index in layer) {
                        var real_layer = layer[stuff_index];
                        var filter_collection = new FilterCollection(real_layer, {});
                        filter_collection.each(function(filter) {
                            if(!(filter.attributes.feature in cleaned_filter)) {
                                cleaned_filter[filter.attributes.feature] = [];
                            }
                            cleaned_filter[filter.attributes.feature].push(filter);
                        });
                    }
                    for(var type_code in cleaned_filter) {
                        cleaned_filter[type_code] = this.format(type_code, cleaned_filter[type_code]);
                    }
                    if(
                        (layer_index == attrs.filters.length - 1) &&
                        (layer.length == 0 || layer[0].length == 0)
                    ) {
                        attrs.empty_fallback = true;
                    } else {
                        attrs.cleaned_filters.push(cleaned_filter);
                    }
                }
            }
            return attrs;
        }
    });
});
