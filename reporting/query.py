METRICS = [
    ('visits', 'Visits', '# of unique visits'),
    ('authorized_visits', 'Authorized Visits', '# of visits that authorized'),
    ('uniq_users_authorized', 'Users Authorized', '# of unique users who authorized'),
    ('auth_fails', 'Authorization Fails', '# of failed authorizations (either via decline or error)'),
    ('visits_generated_faces', 'Visits Generated Faces', '# of visits that had friend suggestions generated'),
    ('visits_shown_faces', 'Visits Shown Faces', '# of visits that had friend suggestions shown to them'),
    ('visits_with_shares', 'Visits With Shares', '# of visits that had at least one share'),
    ('total_shares', 'Total Shares', '# of total shares'),
    ('clickbacks', 'Clickbacks', '# of total clickbacks'),
]

def metric_expressions():
    return ["sum({0}) as {0}".format(slug) for slug, _, _ in METRICS]


def metric_where_fragment():
    return ",\n".join(metric_expressions())

