# -*- coding: utf-8 -*-
"""Utility functionality."""

from datetime import datetime

import dateutil

def datetime_to_timestamp(datetime_obj):
    """Return a timestamp for the given datetime object.

      :param datetime_obj: datetime object to be converted
    :type datetime_obj: datetime.datetime
    :return: timestamp from the passed datetime object
    :rtype: int

    """
    reference = datetime(1970, 1, 1)
    if datetime_obj.tzinfo:
        reference = reference.replace(tzinfo=dateutil.tz.tzutc())

    return int((datetime_obj - reference).total_seconds())
