import csv
import collections
import datetime
import itertools
import json
import numbers
import re

from boto.dynamodb import types as basetypes

# Make boto's generic data types available:
from boto.dynamodb2.types import (
    STRING,
    NUMBER,
    BINARY,
    STRING_SET,
    NUMBER_SET,
    BINARY_SET,
)

from targetshare.models.dynamo import utils


# Exotic types to ease (de)serialization #

def is_null(value):
    # False-y value which is neither numeric nor boolean:
    return not value and not isinstance(value, numbers.Number)


class DataValidationError(Exception):
    pass


class DataType(object):

    def decode(self, value):
        """Convert the given value to the appropriate Python.

        Used when recording original Item values read in from Dynamo, and by
        default when setting Item values. (See `decode_lossy`.)

        """
        raise NotImplementedError

    def decode_lossy(self, value):
        """Convert the given value to the appropriate Python, with lossy mapping.

        Used when setting Item values, whether novel or read in from Dynamo,
        and by default when recording original values from Dynamo. (See `decode`.)

        If your DataType decoding must lose information, such as by applying a
        length limit, this should be done here, rather than in `decode`; that
        method should continue to map with fidelity to the data in Dynamo.

        Otherwise, defining `decode` is sufficient.

        """
        return self.decode(value)

    def __call__(self, *args, **kws):
        """Construct a new instance of the DataType with the given options."""
        return type(self)(*args, **kws)

    def __repr__(self):
        return type(self).__name__.upper().replace('TYPE', '')


class InternalDataTypeExtension(DataType, str):

    internal = None

    def __new__(cls):
        return super(InternalDataTypeExtension, cls).__new__(cls, cls.internal)

    def __getnewargs__(self):
        # str is pickle-able by returning (self,), s.t. the object is reloaded with
        # __new__(cls, self); but we have cls.internal & don't accept
        # initialization arguments:
        return ()


class BoolType(DataType):

    def decode(self, value):
        return value if is_null(value) else bool(value)

BOOL = BoolType()


class DateType(DataType):

    def decode(self, value):
        if is_null(value) or isinstance(value, datetime.date):
            return value
        elif basetypes.is_num(value):
            return utils.epoch_to_date(value)
        raise DataValidationError(
            "Value is not an appropriate date specification: {!r}".format(value))

DATE = DateType()


class DateTimeType(DataType):

    def decode(self, value):
        if is_null(value) or isinstance(value, datetime.datetime):
            return value
        elif basetypes.is_num(value):
            return utils.epoch_to_datetime(value)
        raise DataValidationError(
            "Value is not an appropriate datetime specification: {!r}".format(value))

DATETIME = DateTimeType()


class JsonType(DataType):

    def __init__(self, cls=None):
        self.cls = cls

    def decode(self, value):
        if is_null(value):
            return value

        if isinstance(value, basestring):
            try:
                # Must use OrderedDict to avoid erroneous value drift during
                # decode/encode cycle:
                python = json.loads(value, object_pairs_hook=collections.OrderedDict)
            except ValueError as exc:
                raise DataValidationError(str(exc))
            else:
                if self.cls is None:
                    return python
                else:
                    return self.cls(python)

        try:
            json.dumps(value)
        except TypeError as exc:
            raise DataValidationError(str(exc))
        else:
            return value

JSON = JsonType()


class NumberType(InternalDataTypeExtension):

    internal = NUMBER

    def decode(self, value):
        if not is_null(value) and not basetypes.is_num(value):
            try:
                decimal = basetypes.DYNAMODB_CONTEXT.create_decimal(value)
            except TypeError:
                decimal = None
            if decimal is None or not decimal.is_finite():
                raise DataValidationError(
                    "Value is not an appropriate numeric specification: {!r}".format(value))
            else:
                value = decimal

        return value

NUMBER = NumberType()


COMMA = ','
DOUBLE_NEWLINE = re.compile(r'\r?\n\r?\n')


class AbstractSetType(InternalDataTypeExtension):

    COMMA = COMMA
    DOUBLE_NEWLINE = DOUBLE_NEWLINE

    item_cast = None # optional
    item_type = None # required
    limit = None # optional

    def __new__(cls, delimiter=COMMA):
        self = super(AbstractSetType, cls).__new__(cls)
        self.delimiter = delimiter
        return self

    def decode(self, value):
        return value if is_null(value) else set(self._decode(value))

    def decode_lossy(self, value):
        if is_null(value):
            return value

        decoded = self._decode(value)
        sliced = itertools.islice(decoded, self.limit)
        return set(sliced)

    def _decode(self, value):
        if isinstance(value, basestring):
            value = self.decode_str(value)
        elif hasattr(value, '__iter__'):
            value = self.decode_iter(value)
        else:
            raise DataValidationError("Value is not an appropriate {} specification: {!r}"
                                      .format(self.__class__.__name__, value))

        cast_item = self.item_cast or (lambda item: item)
        return (cast_item(item) for item in value if item)

    def decode_str(self, value):
        if isinstance(self.delimiter, re._pattern_type):
            return (item.strip() for item in self.delimiter.split(value.strip()))

        if self.delimiter == self.COMMA:
            # csv doesn't handle unicode or unquoted newlines
            line = re.sub(r'\s', ' ', value.encode('utf-8'))
            try:
                row = csv.reader([line]).next()
            except csv.Error:
                pass
            else:
                return (item.decode('utf-8').strip() for item in row)

        # delimiter is neither of the above or csv.reader failed:
        return (item.strip() for item in value.strip().split(self.delimiter))

    def decode_iter(self, value):
        if self.item_type is None:
            raise NotImplementedError

        for item in value:
            if not isinstance(item, self.item_type):
                raise DataValidationError(
                    "Instances of {} may only contain instances of {}: {!r}"
                    .format(self.__class__.__name__, self.item_type, value)
                )

            if not item:
                raise DataValidationError(
                    "Set types may not contain empty strings: {!r}".format(value))

        return value


class NumberSetType(AbstractSetType):

    internal = NUMBER_SET
    item_cast = int
    item_type = numbers.Number

NUMBER_SET = NumberSetType()


class StringSetType(AbstractSetType):

    internal = STRING_SET
    item_type = basestring
    limit = 100

STRING_SET = StringSetType()


# TODO: Make DataTypes responsible for encoding rather than / along with Dynamizer
# TODO: (which doesn't know the field type)
# TODO: This would make a big difference below, in saving, and allow for smarter
# TODO: querying (e.g. get_item(fbid='123'))

class Dynamizer(basetypes.Dynamizer):

    def _get_dynamodb_type(self, attr):
        if isinstance(attr, datetime.date):
            return NUMBER
        elif isinstance(attr, (list, dict)):
            return STRING
        return super(Dynamizer, self)._get_dynamodb_type(attr)

    def _encode_n(self, attr):
        if isinstance(attr, datetime.date):
            attr = utils.to_epoch(attr)
        return super(Dynamizer, self)._encode_n(attr)

    def _encode_s(self, attr):
        if isinstance(attr, (list, dict)):
            attr = json.dumps(attr)
        return super(Dynamizer, self)._encode_s(attr)
