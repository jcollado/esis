# -*- coding: utf-8 -*-
"""Utility tools test cases."""

import unittest

from datetime import datetime

import dateutil.tz

from esis.util import datetime_to_timestamp


class DatetimeToTimestampTest(unittest.TestCase):

    """Datetime to timestamp test cases."""

    def test_conversion(self):
        """Naive datetime is correctly converted to a timestamp."""
        datetime_obj = datetime(2010, 1, 1, 12, 0, 0)
        self.assertEqual(datetime_to_timestamp(datetime_obj), 1262347200)

    def test_utc_conversion(self):
        """UTC datetime is correctly converted to timestamp."""
        datetime_obj = datetime(
            2010, 1, 1, 12, 0, 0, tzinfo=dateutil.tz.tzutc())
        self.assertEqual(datetime_to_timestamp(datetime_obj), 1262347200)

    def test_offset_conversion(self):
        """datetime with tzinfo offset is correctly converted to timestamp."""
        datetime_obj = datetime(
            2010, 1, 1, 13, 0, 0,
            tzinfo=dateutil.tz.tzoffset('MyTimezone', 3600))
        self.assertEqual(datetime_to_timestamp(datetime_obj), 1262347200)
