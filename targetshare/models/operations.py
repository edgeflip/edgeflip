"""Common cross-model operations"""
from . import relational


def init_filter(**data):
    """Create a new Filter for the given Client.

    Optionally set up the Filter's FilterFeatures and FilterMeta. FilterFeature data
    should be specified as dictionaries. For example::

        init_filter(client=client, name="myFilter", description="It's great",
                    features=[{'feature': 'foo', 'operator': 'min', 'value': 99}])

    """
    features = data.pop('features', ())
    metadata = data.pop('metadata', ())
    filt = relational.Filter.objects.create(**data)
    if features:
        filt.filterfeature_set.replace(features, replace_all=True)
    if metadata:
        filt.filtermeta_set.replace(metadata, replace_all=True)
    return filt


def init_client(**data):
    """Create a new client in the database and, optionally, set up its Filter,
    ChoiceSet and ClientDefaults.

        init_client(name='myClient', fb_app_name="SaveWhales", fb_app_id="1",
                    domain="savewhales", generate_defaults=True)

    """
    generate_defaults = data.pop('generate_defaults', False)
    client = relational.Client.objects.create(**data)
    if not generate_defaults:
        return client
    # ...
