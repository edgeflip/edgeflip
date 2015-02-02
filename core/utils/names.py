import re

NAME_SUFFIX_PATTERNS = '(I{1,3}|IV|VI{,3}|IX|JR\.?|SR\.?|2ND|3RD|LPN?|RN|LCSW|M\.?D\.?|Ph\.?D\.?|J\.?D\.?)'

suffix = re.compile('^[^a-z0-9]*' + NAME_SUFFIX_PATTERNS + '[^a-z0-9]*$', re.I)


def parse_names(name):
    """Parse a given full name into a length-two sequence consisting of a presumed
    first name and last name.

    """
    parts = re.split(' +', name)

    # Reserve first word for first name:
    first_parts = [parts.pop(0)]

    # Put last word(s) into last name:
    last_parts = []
    while parts:
        part = parts.pop()
        last_parts.append(part)
        if not suffix.match(part):
            break
    last_parts.reverse() # faster than inserting into list

    # Add remainder to first name:
    first_parts.extend(parts)

    return tuple(' '.join(section) for section in (first_parts, last_parts))
