import collections

from gerry import models


def _check_feature(feature):
    if feature not in models.SUPPORTED_FEATURES:
        raise ValueError("Unsupported feature {!r}; try one of: {}"
                         .format(feature, models.SUPPORTED_FEATURES))


def impute_feature(user, feature):
    _check_feature(feature)

    for lookup in models.LOOKUPS:
        try:
            match = lookup.items.lookup_match(user)
        except (lookup.DoesNotExist, models.FeatureMissing):
            value = None
        else:
            value = match.get(feature)

        setattr(user, feature, value)
        if value is not None:
            return value


def bulk_impute(users, feature):
    _check_feature(feature)

    queue = collections.deque(users)
    for lookup in models.LOOKUPS:
        if not queue:
            break # we're done

        # We expect fewer matches than total users in the queue;
        # and, matches don't require group-by, they're already unique;
        # so, construct score look-up table and iterate over users ("once")

        matches = lookup.batch_match(queue)
        iterable = matches.iterable # FIXME
        scores = {match.attrs: match[feature] for match in iterable if feature in match}
        if not scores:
            continue # try the next look-up

        # ...However, we can't alter a collection during iteration;
        # at least, avoid holding two copies of queue in memory at once
        (queue0, queue) = (queue, collections.deque())

        while queue0:
            user = queue0.popleft()
            attrs = lookup.extract_attrs(user)
            try:
                score = scores[attrs]
            except KeyError:
                # No luck; maybe next look-up
                setattr(user, feature, None)
                queue.append(user)
            else:
                # We got a match!
                setattr(user, feature, score)
