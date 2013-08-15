"""Common cross-model operations"""
# TODO: These are ports from the defunct client_db_tools, and their usefulness
# TODO: should be further scrutinized. They're not used by this app, (AFAIK) only by
# TODO: the "client_tools" app, (which currently resides in another repo) --JL
from collections import namedtuple

from . import relational


ClientInit = namedtuple('ClientInit', ('client', 'filter', 'choice_set', 'client_default'))


def init_client(**data):
    """Create a new client in the database and, optionally, set up its Filter,
    ChoiceSet and ClientDefaults.

    For example::

        init_client(
            # client data:
            name='myClient', fb_app_name="SaveWhales", fb_app_id="1", domain="savewhales",
            # specification that associated objects be generated with default data:
            generate_defaults=True
        )

    Returns a "ClientInit" tuple supporting attribute access via "client", "filter",
    "choice_set" and "client_default"::

        (Client(...), Filter(...), ChoiceSet(...), ClientDefault(...))

    """
    generate_defaults = data.pop('generate_defaults', False)
    client = relational.Client.objects.create(**data)

    if generate_defaults:
        # Set up default client data #
        default_name = 'edgeflip default'
        default_desc = 'Default element created by edgeflip'

        # Create Filter, ChoiceSet, ChoiceSetFilters and ClientDefault:
        filt = client.filters.create(name=default_name, description=default_desc)
        choice_set = client.choicesets.create(name=default_name, description=default_desc)
        choice_set.choicesetfilters.create(filter=filt, url_slug='all')
        client_default = client.clientdefaults.create(filter=filt, choice_set=choice_set)
    else:
        filt = choice_set = client_default = None

    return ClientInit(client, filt, choice_set, client_default)


def init_button_style(**data):
    """Create a new ButtonStyle and ButtonStyleFile.

    For example::

        init_button_style(
            # button style data:
            client=Client(...), name="My Button Style", description="It rocks",
            # button style file data:
            html_template='button.html',
        )

    """
    html_template = data.pop('html_template', None)
    if not html_template:
        raise ValueError("Must specify an HTML template")
    button_style = relational.ButtonStyle.objects.create(**data)
    button_style.buttonstylefiles.create(html_template=html_template)
    return button_style
