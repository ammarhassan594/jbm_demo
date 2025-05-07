from collections import defaultdict
import math
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY, WEEKLY
from functools import partial
from itertools import chain
from pytz import timezone, utc

from odoo import api, fields, models, _
from odoo.addons.base.models.res_partner import _tz_get
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools.float_utils import float_round

from odoo.tools import date_utils, float_utils

# Default hour per day value. The one should
# only be used when the one from the calendar
# is not available.
HOURS_PER_DAY = 8
# This will generate 16th of days
ROUNDING_FACTOR = 16

def float_to_time(hours):
    """ Convert a number of hours into a time object. """
    if hours == 24.0:
        return time.max
    fractional, integral = math.modf(hours)
    return time(int(integral), int(float_round(60 * fractional, precision_digits=0)), 0)

def _boundaries(intervals, opening, closing):
    """ Iterate on the boundaries of intervals. """
    for start, stop, recs in intervals:
        if start < stop:
            yield (start, opening, recs)
            yield (stop, closing, recs)

class Intervals(object):
    """ Collection of ordered disjoint intervals with some associated records.
        Each interval is a triple ``(start, stop, records)``, where ``records``
        is a recordset.
    """
    def __init__(self, intervals=()):
        self._items = []
        if intervals:
            # normalize the representation of intervals
            append = self._items.append
            starts = []
            recses = []
            for value, flag, recs in sorted(_boundaries(intervals, 'start', 'stop')):
                if flag == 'start':
                    starts.append(value)
                    recses.append(recs)
                else:
                    start = starts.pop()
                    if not starts:
                        append((start, value, recses[0].union(*recses)))
                        recses.clear()

    def __bool__(self):
        return bool(self._items)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __reversed__(self):
        return reversed(self._items)

    def __or__(self, other):
        """ Return the union of two sets of intervals. """
        return Intervals(chain(self._items, other._items))

    def __and__(self, other):
        """ Return the intersection of two sets of intervals. """
        return self._merge(other, False)

    def __sub__(self, other):
        """ Return the difference of two sets of intervals. """
        return self._merge(other, True)

    def _merge(self, other, difference):
        """ Return the difference or intersection of two sets of intervals. """
        result = Intervals()
        append = result._items.append

        # using 'self' and 'other' below forces normalization
        bounds1 = _boundaries(self, 'start', 'stop')
        bounds2 = _boundaries(other, 'switch', 'switch')

        start = None                    # set by start/stop
        recs1 = None                    # set by start
        enabled = difference            # changed by switch
        for value, flag, recs in sorted(chain(bounds1, bounds2)):
            if flag == 'start':
                start = value
                recs1 = recs
            elif flag == 'stop':
                if enabled and start < value:
                    append((start, value, recs1))
                start = None
            else:
                if not enabled and start is not None:
                    start = value
                if enabled and start is not None and start < value:
                    append((start, value, recs1))
                enabled = not enabled

        return result

class InheritResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    allow_flexible_hours = fields.Boolean(string="Allow Flexible Hours")
    max_check_in_hour = fields.Float(string="Check In Max Hour")

    # customize duration value to work with flexible hours logic
    def _attendance_intervals_batch(self, start_dt, end_dt, resources=None, domain=None, tz=None):
        """ Return the attendance intervals in the given datetime range.
            The returned intervals are expressed in specified tz or in the resource's timezone.
        """
        assert start_dt.tzinfo and end_dt.tzinfo
        self.ensure_one()
        combine = datetime.combine
        required_tz = tz

        if not resources:
            resources = self.env['resource.resource']
            resources_list = [resources]
        else:
            resources_list = list(resources) + [self.env['resource.resource']]
        resource_ids = [r.id for r in resources_list]
        domain = domain if domain is not None else []
        domain = expression.AND([domain, [
            ('calendar_id', '=', self.id),
            ('resource_id', 'in', resource_ids),
            ('display_type', '=', False),
        ]])

        # for each attendance spec, generate the intervals in the date range
        cache_dates = defaultdict(dict)
        cache_deltas = defaultdict(dict)
        result = defaultdict(list)
        for attendance in self.env['resource.calendar.attendance'].search(domain):
            for resource in resources_list:
                # express all dates and times in specified tz or in the resource's timezone
                tz = required_tz if required_tz else timezone((resource or self).tz)
                if (tz, start_dt) in cache_dates:
                    start = cache_dates[(tz, start_dt)]
                else:
                    start = start_dt.astimezone(tz)
                    cache_dates[(tz, start_dt)] = start
                if (tz, end_dt) in cache_dates:
                    end = cache_dates[(tz, end_dt)]
                else:
                    end = end_dt.astimezone(tz)
                    cache_dates[(tz, end_dt)] = end

                start = start.date()
                if attendance.date_from:
                    start = max(start, attendance.date_from)
                until = end.date()
                if attendance.date_to:
                    until = min(until, attendance.date_to)
                if attendance.week_type:
                    start_week_type = self.env['resource.calendar.attendance'].get_week_type(start)
                    if start_week_type != int(attendance.week_type):
                        # start must be the week of the attendance
                        # if it's not the case, we must remove one week
                        start = start + relativedelta(weeks=-1)
                weekday = int(attendance.dayofweek)

                if self.two_weeks_calendar and attendance.week_type:
                    days = rrule(WEEKLY, start, interval=2, until=until, byweekday=weekday)
                else:
                    days = rrule(DAILY, start, until=until, byweekday=weekday)

                for day in days:
                    # We need to exclude incorrect days according to re-defined start previously
                    # with weeks=-1 (Note: until is correctly handled)
                    if (self.two_weeks_calendar and attendance.date_from and attendance.date_from > day.date()):
                        continue
                    # attendance hours are interpreted in the resource's timezone
                    hour_from = attendance.hour_from
                    if (tz, day, hour_from) in cache_deltas:
                        dt0 = cache_deltas[(tz, day, hour_from)]
                    else:
                        dt0 = tz.localize(combine(day, float_to_time(hour_from)))
                        cache_deltas[(tz, day, hour_from)] = dt0

                    hour_to = attendance.hour_to

                    if self.allow_flexible_hours:
                        hour_to = attendance.hour_to + self.max_check_in_hour

                    if (tz, day, hour_to) in cache_deltas:
                        dt1 = cache_deltas[(tz, day, hour_to)]
                    else:
                        dt1 = tz.localize(combine(day, float_to_time(hour_to)))
                        cache_deltas[(tz, day, hour_to)] = dt1
                    result[resource.id].append((max(cache_dates[(tz, start_dt)], dt0), min(cache_dates[(tz, end_dt)], dt1), attendance))
        return {r.id: Intervals(result[r.id]) for r in resources_list}