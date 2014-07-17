METRICS = [
    ('initial_redirects', 'Clicks', '# of visits that were presented with the authorization page'),
    ('authorized_visits', 'Authorized Visits', '# of visits with successful authorizations, either via new or previous authorization of the app'),
    ('failed_visits', 'Failed Visits', '# of visits that resulted in either the authorization being refused or the visit being abandoned (e.g., the browser window was closed)'),
    ('uniq_users_authorized', 'Unique Authorized Visitors', '# of unique visitors with one or more authorized visits'),
    ('visits_shown_faces', 'Visits Shown Suggestions', '# of visits that resulted in a user being show friend suggestions'),
    ('visits_with_shares', 'Visits Permitting Share', '# of visits that clicked to share with at least one friend and additionally authorized the app to post the message to their walls'),
    ('total_shares', 'Audience Reached', 'the total audience reached as a result of each authorized share reaching one or more friends'),
    ('clickbacks', 'Clickbacks', '# of clicks on the shared content by the audience reached'),
]

def metric_expressions():
    return ["sum({0}) as {0}".format(slug) for slug, _, _ in METRICS]


def metric_where_fragment():
    return ",\n".join(metric_expressions())

