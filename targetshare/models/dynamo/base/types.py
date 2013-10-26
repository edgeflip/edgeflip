import datetime
import numbers

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

    def load(self, value):
        raise NotImplementedError

    def validate(self, value):
        raise NotImplementedError

    def __repr__(self):
        return type(self).__name__.upper().replace('TYPE', '')


class DateType(DataType):

    def load(self, value):
        if isinstance(value, datetime.date):
            return value
        return utils.epoch_to_date(value)

    def validate(self, value):
        if (
            is_null(value) or
            basetypes.is_num(value) or
            isinstance(value, datetime.date)
        ):
            return
        raise DataValidationError(
            "Value is not an appropriate date specification: {!r}".format(value))


class DateTimeType(DataType):

    def load(self, value):
        if isinstance(value, datetime.date):
            return value
        return utils.epoch_to_datetime(value)

    def validate(self, value):
        if (
            is_null(value) or
            basetypes.is_num(value) or
            isinstance(value, datetime.datetime)
        ):
            return
        raise DataValidationError(
            "Value is not an appropriate datetime specification: {!r}".format(value))


DATE = DateType()
DATETIME = DateTimeType()


class Dynamizer(basetypes.Dynamizer):

    def _get_dynamodb_type(self, attr):
        if isinstance(attr, datetime.date):
            return NUMBER
        return super(Dynamizer, self)._get_dynamodb_type(attr)

    def _encode_n(self, attr):
        if isinstance(attr, datetime.date):
            attr = utils.to_epoch(attr)
        return super(Dynamizer, self)._encode_n(attr)
