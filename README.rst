
================
django-xvalidate
================

django-xvalidate allows you to declare cross-field validators within a
Django model.

As an example, consider a Django model named `Event`.

    from django.db import models

    class Event(models.Model):
        title = models.CharField(max_length=255)
        start_date = models.DateField()
        end_date = models.DateField()

django-xvalidate allows you to declare that the start date precedes the end
date as follows:

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

`XValidatedModel` ensures that this specification is maintained invoking
`Event.clean()` and raises `ValidationError` as appropriate.
