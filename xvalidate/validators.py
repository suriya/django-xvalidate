

import six
import abc
import decimal
import operator
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models import (ForeignKey, OneToOneField, )
from django.db.models.fields import FieldDoesNotExist
from django.utils.decorators import classonlymethod
from django.core import checks

__all__ = (
    'XEq', 'XNe',  'XLt',  'XGt',  'XLe',  'XGe', 'XImplies', 'XValue',
    'XTrue', 'XFalse', 'XNone', 'XNotNone', 'XField', 'XF',
)


class AbnormalValues(object):
    NULL_REF = object()
    TYPE_ERROR = object()

    @classonlymethod
    def is_abnormal(cls, value):
        return (value in [cls.NULL_REF, cls.TYPE_ERROR])


def get_model_field(model, fieldspec):
    """
    Lookup a model's field traversing double underscores.

    fieldspec is usually a string representing a field specification.
    fieldspec can also be a tuple, in which case we get the spec from its
    contents.

    Traverses ForeignKey and OneToOneField relations. Returns a field
    object.

    Returns None if the lookup is invalid.

    Adapted from: https://github.com/alex/django-filter/blob/73a391adb27ef31047faf1a3497b562fd071f6cb/django_filters/filterset.py#L84 # noqa
    """
    opts = model._meta
    if not isinstance(fieldspec, tuple):
        fieldspec = fieldspec.split(LOOKUP_SEP)
    rel = None
    for (i, name) in enumerate(fieldspec):
        if (i > 0):
            if not isinstance(rel, (ForeignKey, OneToOneField)):
                return None
            opts = rel.related_model._meta
        try:
            (rel, _, _, _) = opts.get_field_by_name(name)
        except FieldDoesNotExist:
            return None
    return rel


def get_field(obj, fieldspec):
    """
    Get a field of 'obj'. fieldspec could traverse related fields through
    double underscore '__'.
    """
    for f in fieldspec.split(LOOKUP_SEP):
        if (obj is None):
            return AbnormalValues.NULL_REF
        if not isinstance(obj, models.Model):
            raise TypeError('Expected a Django model')
        obj = getattr(obj, f, None)
    return obj


class XValidateExpr(six.with_metaclass(abc.ABCMeta, object)):
    def __init__(self, message={}, *args, **kwargs):
        if isinstance(message, six.string_types):
            message = {
                self._get_field_for_message(): message
            }
        self.message = message

    @abc.abstractmethod
    def _clean(self, instance):
        pass

    @abc.abstractmethod
    def _check(self, model, **kwargs):
        pass

    @classmethod
    def make_xvalidateexpr(cls, o):
        """
        Create an XValidateExpr object from primitive objects.
        """
        if isinstance(o, XValidateExpr):
            return o
        if isinstance(o, six.string_types):
            return XField(o)
        return XValue.make_xvalue(o)

    def _get_field_for_message(self):
        """
        Lookup the field for a message, if it is not specified.
        """
        raise ValueError('Could not find field for message.')

    def __inv__(self):
        return XFalse(self)

    def or_(self, e2):
        return XOr(self, e2)

    def and_(self, e2):
        return XAnd(self, e2)

    def __ne__(self, e2):
        return XNe(self, e2)

    def __eq__(self, e2):
        return XEq(self, e2)

    def __le__(self, e2):
        return XLe(self, e2)

    def __ge__(self, e2):
        return XGe(self, e2)

    def __lt__(self, e2):
        return XLt(self, e2)

    def __gt__(self, e2):
        return XGt(self, e2)


class XField(XValidateExpr):
    def __init__(self, fieldspec, *args, **kwargs):
        if not isinstance(fieldspec, six.string_types):
            raise TypeError("In XField.__init__: 'fieldspec' must be a string")
        self.fieldspec = fieldspec
        super(XField, self).__init__(*args, **kwargs)

    def _get_field_for_message(self):
        return self.fieldspec.split(LOOKUP_SEP)[0]

    def _check(self, model):
        if get_model_field(model, self.fieldspec):
            return []
        return [
            checks.Error(
                "XField '{}' in model '{}'".format(self.fieldspec, model.__name__),
                hint="Check for typos in the field specification",
                obj=model,
                id='xvalidate.E003',
            )
        ]

    def _clean(self, instance):
        return {
            'value': get_field(instance, self.fieldspec),
            'message': self.message,
        }
XF = XField


class XValue(XValidateExpr):
    def __init__(self, value, *args, **kwargs):
        if self.can_make_xvalue(value):
            self.value = value
        else:
            raise TypeError("Unhandled type in XValue.__init__: {}".format(type(value)))
        super(XValue, self).__init__(*args, **kwargs)

    @classmethod
    def can_make_xvalue(cls, o):
        number_types = six.integer_types + (decimal.Decimal, float, )
        return isinstance(o, number_types)

    @classmethod
    def make_xvalue(cls, o):
        if cls.can_make_xvalue(o):
            return XValue(o)
        raise TypeError("Unhandled type in make_xvalue: {}".format(type(o)))

    def _check(self, model):
        return []

    def _clean(self, instance):
        return {
            'value': self.value,
            'message': self.message,
        }


class XBooleanExpr(XValidateExpr):
    @abc.abstractproperty
    def operator_func(self):
        pass

    def __init__(self, left, right, *args, **kwargs):
        self.left = XValidateExpr.make_xvalidateexpr(left)
        self.right = XValidateExpr.make_xvalidateexpr(right)
        super(XBooleanExpr, self).__init__(*args, **kwargs)

    def _get_field_for_message(self):
        return self.left._get_field_for_message()

    def _check(self, model, **kwargs):
        return (
            self.left._check(model, **kwargs) +
            self.right._check(model, **kwargs)
        )

    def _clean(self, instance):
        cchildren = [self.left._clean(instance), self.right._clean(instance)]
        cchildren = [cc for cc in cchildren if (not AbnormalValues.is_abnormal(cc['value']))]
        if len(cchildren) < 2:
            satisfied = True
        else:
            (left, right) = cchildren
            try:
                satisfied = self.operator_func(left['value'], right['value'])
            except TypeError:
                if (left is None) or (right is None):
                    satisfied = AbnormalValues.TYPE_ERROR
                else:
                    raise
        return {
            'value': satisfied,
            'message': self.message
        }


class XUnaryExpr(XValidateExpr):
    @abc.abstractproperty
    def operator_func(self):
        pass

    def __init__(self, left, *args, **kwargs):
        self.left = XValidateExpr.make_xvalidateexpr(left)
        super(XUnaryExpr, self).__init__(*args, **kwargs)

    def _check(self, model, **kwargs):
        return self.left._check(model, **kwargs)

    def _get_field_for_message(self):
        return self.left._get_field_for_message()

    def _clean(self, instance):
        cchildren = [self.left._clean(instance), ]
        cchildren = [cc for cc in cchildren if (not AbnormalValues.is_abnormal(cc['value']))]
        if len(cchildren) < 1:
            satisfied = True
        else:
            (left, ) = cchildren
            satisfied = self.operator_func(left['value'])
        return {
            'value': satisfied,
            'message': self.message
        }


class XTrue(XUnaryExpr):
    operator_func = operator.truth


class XFalse(XUnaryExpr):
    def operator_func(self, x):
        return not x


class XNone(XUnaryExpr):
    def operator_func(self, x):
        return (x is None)


class XNotNone(XUnaryExpr):
    def operator_func(self, x):
        return (x is not None)


class XEq(XBooleanExpr):
    operator_func = operator.eq


class XNe(XBooleanExpr):
    operator_func = operator.ne


class XLt(XBooleanExpr):
    operator_func = operator.lt


class XGt(XBooleanExpr):
    operator_func = operator.gt


class XLe(XBooleanExpr):
    operator_func = operator.le


class XGe(XBooleanExpr):
    operator_func = operator.ge


class XAnd(XBooleanExpr):
    def operator_func(self, a, b):
        return (a and b)


class XOr(XBooleanExpr):
    def operator_func(self, a, b):
        return (a or b)


class XImplies(XBooleanExpr):
    def operator_func(self, a, b):
        return (not a or b)
