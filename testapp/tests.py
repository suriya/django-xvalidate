
import datetime
from django.test import TestCase
from django.core.exceptions import (ValidationError, NON_FIELD_ERRORS)

from .models import Organizer, Event

TODAY = datetime.date.today()
YESTERDAY = TODAY - datetime.timedelta(days=1)
TOMORROW = TODAY + datetime.timedelta(days=1)


class EventTestCase(TestCase):
    def setUp(self):
        self.active = Organizer(name='Active')
        self.active.save()
        self.inactive = Organizer(name='In Active', is_active=False)
        self.inactive.save()

    def test_model_check(self):
        self.assertEqual(Event.check(), [])

    def test_organizer(self):
        with self.assertRaises(ValidationError) as context:
            Event(
                organizer=self.inactive,
                title='Our inactive event',
                start_date=TODAY,
                end_date=TOMORROW).full_clean()
        self.assertIn(
            'The Organizer is not active',
            context.exception.message_dict['organizer'][0])
        Event(
            organizer=self.active,
            title='Our active event',
            start_date=TODAY,
            end_date=TOMORROW).full_clean()

    def test_dates(self):
        with self.assertRaises(ValidationError) as context:
            Event(
                organizer=self.active,
                title='Our inconsistent event',
                start_date=TODAY,
                end_date=YESTERDAY).full_clean()
        self.assertIn(
            'Validation failed, but no message specified',
            context.exception.message_dict[NON_FIELD_ERRORS][0])
