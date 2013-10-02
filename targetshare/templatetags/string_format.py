from django import template


register = template.Library()


@register.filter(name='lexlist')
def lexical_list(sequence, final_comma=False):
    """Join a list in an English-friendly manner.

    >>> lexical_list(['Bob'], True)
    'Bob'
    >>> lexical_list(['Bob', 'Bill'], True)
    'Bob and Bill'
    >>> lexical_list(['Bob', 'Bill', 'Sandy'], True)
    'Bob, Bill, and Sandy'
    >>> lexical_list(['Bob', 'Bill', 'Sandy'])
    'Bob, Bill and Sandy'

    """
    body = sequence[:-1]
    tail = sequence[-1]

    if body:
        if final_comma and len(body) > 1:
            connector = ', and '
        else:
            connector = ' and '
        head = ', '.join(body)
        return connector.join([head, tail])

    return tail


@register.filter
def oxford(sequence):
    return lexical_list(sequence, True)
