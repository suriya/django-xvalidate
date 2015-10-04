

from django.db import models
from django.utils.decorators import classonlymethod
from django.core.exceptions import (ValidationError, NON_FIELD_ERRORS)
from django.core import checks
from .validators import AbnormalValues

__all__ = (
    'XValidatedModel',
)


class XValidatedModel(models.Model):
    class Meta:
        abstract = True

    class XVMeta:
        spec = []

    @classmethod
    def _check_xvmeta(cls, **kwargs):
        if not issubclass(cls.XVMeta, XValidatedModel.XVMeta):
            yield checks.Error(
                "Model's XVMeta should inherit from XValidatedModel.XVMeta",
                hint="Use XVMeta(XValidatedModel.XVMeta) in the model's definition",
                obj=cls,
                id='xvalidate.E001',
            )
        for name in dir(cls.XVMeta):
            if name.startswith('_'):
                continue
            if name not in dir(XValidatedModel.XVMeta):
                yield checks.Error(
                    "Unexpected field '{}' in XVMeta definition".format(name),
                    hint="Check for typos in XVMeta",
                    obj=cls,
                    id='xvalidate.E002',
                )

    def _raise_validation_error_if_needed(self, result):
        value = result['value']
        if AbnormalValues.is_abnormal(value):
            return
        if not value:
            message = result['message']
            if not message:
                message = {
                    NON_FIELD_ERRORS: "Validation failed, but no message specified"
                }
            raise ValidationError(message)

    def _clean_xvmeta(self):
        for s in self.XVMeta.spec:
            result = s._clean(self)
            self._raise_validation_error_if_needed(result)

    @classonlymethod
    def check(cls, **kwargs):
        errors = super(XValidatedModel, cls).check(**kwargs)
        errors.extend(cls._check_xvmeta(**kwargs))
        for s in cls.XVMeta.spec:
            errors.extend(s._check(cls))
        return errors

    def clean(self):
        super(XValidatedModel, self).clean()
        self._clean_xvmeta()
