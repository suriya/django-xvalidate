
from django.db import models
from xvalidate import XValidatedModel, XF, XTrue


class Organizer(XValidatedModel, models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)


class Event(XValidatedModel, models.Model):
    organizer = models.ForeignKey(Organizer)
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()

    class XVMeta(XValidatedModel.XVMeta):
        spec = [
            XTrue('organizer__is_active', message='The Organizer is not active'),
            XF('start_date') <= 'end_date',
        ]
