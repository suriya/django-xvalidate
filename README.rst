
================
django-xvalidate
================

.. image:: https://travis-ci.org/suriya/django-xvalidate.svg?branch=master
    :target: https://travis-ci.org/suriya/django-xvalidate
.. image:: https://coveralls.io/repos/suriya/django-xvalidate/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/suriya/django-xvalidate?branch=master
.. image:: https://img.shields.io/pypi/v/django-xvalidate.svg
    :target: https://pypi.python.org/pypi/django-xvalidate
    :alt: Latest PyPI version

django-xvalidate allows you to declare cross-field validators within a
Django model.

As an example, consider a Django model named :code:`Event`.

.. code:: python

  from django.db import models

  class Event(models.Model):
      title = models.CharField(max_length=255)
      start_date = models.DateField()
      end_date = models.DateField()

django-xvalidate allows you to declare that the start date precedes the end
date as follows:

.. code:: python

  from django.db import models
  from xvalidate import XValidatedModel, XLe

  class Event(XValidatedModel, models.Model):
      title = models.CharField(max_length=255)
      start_date = models.DateField()
      end_date = models.DateField()

      class XVMeta(XValidatedModel.XVMeta):
          spec = [
              XLe('start_date', 'end_date').message(
                  'The start date should precede the end date')
          ]

:code:`XValidatedModel` ensures that this specification is maintained
invoking :code:`Event.clean()` and raises :code:`ValidationError` as
appropriate.

Why use django-xvalidate?
-------------------------
django-xvalidate allows you to specify how to validate your model instances
in a more declarative manner than writing imperative code within your
:code:`clean()` methods. Without django-xvalidate you would have to
implement the above example as

.. code:: python

    def clean(self):
        super(Event, self).clean()
        if (self.start_date is not None) and (self.end_date is not None):
            if (self.end_date < self.start_date):
                raise ValidationError('The start date should precede the end date')

With a more declarative format we have the option at some point in the
future to automate the creation of test data that passes (or fails)
validation.

django-xvalidate comes some operator overloading that brings syntactic
sugar to your declarations making them very easy to read. For instance,
you could specify:

.. code:: python

    ((XF('end_date') - 'start_date') > datetime.timedelta(days=4)).message(
        'Event should last at least 5 days'
    )

django-xvalidate also allows the use of Django's double-underscore (`__`)
syntax to dereference related objects, enabling succinct definitions such
as the following

.. code:: python

    (XF('registration_date') <= 'event__end_date').message(
        'Must register before the event ends')
