import decimal


def make_version(value, max_digits=3, decimal_places=1):
    if not isinstance(value, decimal.Decimal):
        value = decimal.Decimal(value)

    context = decimal.getcontext().copy()
    context.prec = max_digits
    roundto = decimal.Decimal('.1') ** decimal_places

    return context.quantize(value, roundto)
