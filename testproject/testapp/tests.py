
import datetime
from django.test import TestCase
from django.core.exceptions import ValidationError

from .models import Event

TODAY = datetime.date.today()
YESTERDAY = TODAY - datetime.timedelta(days=1)
TOMORROW = TODAY + datetime.timedelta(days=1)


class EventTestCase(TestCase):
    def test_events(self):
        Event(
            title='Our good event',
            start_date=TODAY,
            end_date=TOMORROW).full_clean()
        with self.assertRaises(ValidationError) as context:
            Event(
                title='Our bad event',
                start_date=TODAY,
                end_date=YESTERDAY).full_clean()
        self.assertIn('The start date should precede the end date',
            context.exception.message_dict['start_date'][0])
