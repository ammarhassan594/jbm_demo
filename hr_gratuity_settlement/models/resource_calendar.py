# -*- coding: utf-8 -*-
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY, WEEKLY
from pytz import timezone, utc

from odoo import api, fields, models, _
from odoo.osv import expression

class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    def _work_intervals_days(self, start_dt, end_dt, resource=None, domain=None):
        """ Return the attendance intervals in the given datetime range.
            The returned intervals are expressed in the resource's timezone.
        """
        # assert start_dt.tzinfo and end_dt.tzinfo
        combine = datetime.combine

        resource_ids = [resource.id, False] if resource else [False]
        domain = domain if domain is not None else []
        domain = expression.AND([domain, [
            ('calendar_id', '=', self.id),
            ('resource_id', 'in', resource_ids),
            ('display_type', '=', False),
        ]])

        # express all dates and times in the resource's timezone
        tz = timezone((resource or self).tz)
        start_dt = start_dt.astimezone(tz)
        end_dt = end_dt.astimezone(tz)

        # for each attendance spec, generate the intervals in the date range
        result = []
        for attendance in self.env['resource.calendar.attendance'].search(domain):
            start = start_dt.date()
            if attendance.date_from:
                start = max(start, attendance.date_from)
            until = end_dt.date()
            if attendance.date_to:
                until = min(until, attendance.date_to)
            if attendance.week_type:
                start_week_type = int(math.floor((start.toordinal() - 1) / 7) % 2)
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
                result.append(day)

        return result