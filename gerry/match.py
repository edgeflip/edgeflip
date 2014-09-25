import collections

from gerry import models


SUPPORTED_FEATURES = {'gotv_score', 'persuasion_score'}

LOOKUPS = (models.StateCityNameVoter, models.StateNameVoter)


def _check_feature(feature):
    if feature not in SUPPORTED_FEATURES:
        raise ValueError("Unsupported feature {!r}; try one of: {}"
                         .format(feature, SUPPORTED_FEATURES))


def impute_feature(user, feature):
    _check_feature(feature)

    for lookup in LOOKUPS:
        try:
            match = lookup.items.lookup_match(user)
        except (lookup.DoesNotExist, models.FeatureMissing):
            pass
        else:
            value = match[feature]
            setattr(user, feature, value)
            return value


def bulk_impute(users, feature):
    _check_feature(feature)

    queue = collections.deque(users)
    for lookup in LOOKUPS:
        if not queue:
            break # we're done

        # We expect fewer matches than users in the queue;
        # and, matches don't require group-by, they're already unique;
        # so, iterate over users and construct score look-up table:

        # FIXME: extract_attrs is being used in two different ways
        matches = lookup.batch_match(queue)
        iterable = matches.iterable # FIXME
        scores = {match.attrs: match[feature] for match in iterable}
        if not scores:
            continue # try the next look-up

        # However, we can't alter a collection during iteration;
        # at least, avoid holding two copies of queue in memory at once:
        (queue0, queue) = (queue, collections.deque())

        while queue0:
            user = queue0.popleft()
            attrs = lookup.extract_attrs(user)
            try:
                score = scores[attrs]
            except KeyError:
                # No luck; maybe next look-up
                queue.append(user)
            else:
                # We got a match!
                setattr(user, feature, score)


        # Method one #
#        iterable = matches.iterable # FIXME
#        try:
#            head = next(iterable)
#        except StopIteration:
#            continue
#
#        groups = collections.defaultdict(list)
#        for user in queue:
#            attrs = lookup.extract_attrs(user)
#            groups[attrs].append(user)
#
#        for match in itertools.chain((head,), iterable):
#            value = match[feature]
#            for user in groups.get(match.attrs, ()):
#                setattr(user, feature, value)
#                queue.remove(user)
