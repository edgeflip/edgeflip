import csv
import datetime
import json
import numbers
import re

from decimal import Decimal
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

        Used when setting Item values, whether novel or read in from Dynamo.

        """
        raise NotImplementedError

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

    def decode(self, value):
        if is_null(value):
            return value

        if isinstance(value, basestring):
            try:
                return json.loads(value)
            except ValueError as exc:
                raise DataValidationError(str(exc))

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
DOUBLE_NEWLINE = '\n\n'


class NumberSetType(InternalDataTypeExtension):

    internal = NUMBER_SET

    COMMA = COMMA
    DOUBLE_NEWLINE = DOUBLE_NEWLINE

    def __new__(cls, delimiter=COMMA):
        self = super(NumberSetType, cls).__new__(cls)
        self.delimiter = delimiter
        return self

    def decode(self, value):
        if is_null(value):
            return value

        if isinstance(value, basestring):
            if self.delimiter == self.COMMA:
                # csv doesn't handle unicode or unquoted newlines
                line = re.sub(r'\s', ' ', value.encode('utf-8'))
                items = csv.reader([line]).next()
            else:
                items = (item.strip() for item in value.strip().split(self.delimiter))

            return {int(item) for item in items if item}

        if hasattr(value, '__iter__'):
            if not all(isinstance(item, numbers.Number) for item in value):
                raise DataValidationError(
                    "Number set may not contain non-numbers: {!r}".format(value))

            return value if isinstance(value, (set, frozenset)) else set(value)

        raise DataValidationError(
            "Value is not an appropriate string set specification: {!r}".format(value))

NUMBER_SET = NumberSetType()


class StringSetType(InternalDataTypeExtension):

    internal = STRING_SET

    COMMA = COMMA
    DOUBLE_NEWLINE = DOUBLE_NEWLINE

    def __new__(cls, delimiter=COMMA):
        self = super(StringSetType, cls).__new__(cls)
        self.delimiter = delimiter
        return self

    def decode(self, value):
        if is_null(value):
            return value

        if isinstance(value, basestring):
            if self.delimiter == self.COMMA:
                # csv doesn't handle unicode or unquoted newlines
                line = re.sub(r'\s', ' ', value.encode('utf-8'))
                row = csv.reader([line]).next()
                return {item.decode('utf-8').strip() for item in row}
            else:
                items = (item.strip() for item in value.strip().split(self.delimiter))
                return set(item for item in items if item)

        if hasattr(value, '__iter__'):
            if not all(isinstance(item, basestring) for item in value):
                raise DataValidationError(
                    "String set may not contain non-strings: {!r}".format(value))

            return value if isinstance(value, (set, frozenset)) else set(value)

        raise DataValidationError(
            "Value is not an appropriate string set specification: {!r}".format(value))

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
