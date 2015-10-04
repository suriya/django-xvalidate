
from django.db import models
from xvalidate import XValidatedModel, XLe


class Event(XValidatedModel, models.Model):
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()

    class XVMeta(XValidatedModel.XVMeta):
        spec = [
            XLe('start_date', 'end_date',
                message='The start date should precede the end date')
        ]
