"""Common cross-model operations"""
# TODO: These are ports from the defunct client_db_tools, and their usefulness
# TODO: should be further scrutinized. They're barely used by this app, and
# TODO: otherwise only by the "client_tools" app, (AFAIK) --JL
import logging
from collections import namedtuple

from . import relational


LOG = logging.getLogger(__name__)

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


def check_CDFs(tupes):
    """Takes tuples of (id, CDF Probability) and ensures the CDF is well-defined."""
    probs = sorted(t[1] for t in tupes)
    if min(probs) <= 0:
        raise CDFProbsError("Zero or negative probabilities detected")
    if max(probs) != 1.0:
        raise CDFProbsError("Max probability is not 1.0")
    if len(probs) != len(set(probs)):
        raise CDFProbsError("Duplicate values found in CDF")


class CDFProbsError(Exception):
    """CDF defined by provided experimental probabilities is not well-defined"""
    pass


class TieredEdges(object):
    """Quick little class to hold tuples of edges in different tiers
    and return useful things like a list of secondary Id's as well
    as the ability to re-rank the edges within the tiers"""

    def __init__(self, edges=None, **kwargs):
        """Initialize the object with the top tier"""
        self.tiers = []
        if kwargs:
            edges = edges or []
            kwargs['edges'] = edges
            self.tiers.append(kwargs)

    def __len__(self):
        return len([e for t in self.tiers for e in t['edges']])

    def appendTier(self, edges, **kwargs):
        """Append a new tier to the end"""
        edges = edges or []
        kwargs['edges'] = edges
        self.tiers.append(kwargs)

    def edges(self):
        return [e for t in self.tiers for e in t['edges']]

    def secondaries(self):
        return [e.secondary for t in self.tiers for e in t['edges']]

    def secondaryIds(self):
        return [e.secondary.id for t in self.tiers for e in t['edges']]

    def rerankEdges(self, new_edge_ranking):
        """Re-ranks the edges within the tiers. For instance, if
        the tiers were generated using px3 scores but px4 has now
        become available, we can maintain the tiers while providing
        a better order within them.

        """
        for tier in self.tiers:
            edge_list = tier['edges'][:]    # copying - need the original order below
            tier_edge_ids = set(e.secondary.id for e in edge_list)
            new_order = []

            for e in new_edge_ranking:
                if e.secondary.id in tier_edge_ids:
                    new_order.append(e)
                    tier_edge_ids.remove(e.secondary.id)

            if tier_edge_ids:
                # the new ranking was missing some edges. Note it in
                # the logs, then iterate through the original order and
                # append the remaining edges to the end of the list
                LOG.info("%s edges missing from new edge rankings for user %s!",
                         len(tier_edge_ids), edge_list[0].primary.id)
                for e in edge_list:
                    if e.secondary.id in tier_edge_ids:
                        new_order.append(e)
                        tier_edge_ids.remove(e.secondary.id)

            tier['edges'] = new_order
