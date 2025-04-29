from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime


class EbsCalendarMeetingRoom(models.Model):
    _name = 'ebs.calendar.meeting.room'
    _description = 'EBS Calender Meeting Room'

    code = fields.Char("Code")
    name = fields.Char("Name")
    location = fields.Char("Location")
    event_ids = fields.One2many('calendar.event', 'room_id', string="Events")
    count_meeting = fields.Integer('Meeting', compute="compute_meeting_count")

    def compute_meeting_count(self):
        for rec in self:
            rec.count_meeting = self.env['calendar.event'].search_count([('room_id', '=', rec.id)])

    def get_meeting(self):
        self.ensure_one()
        action = self.env.ref('calendar.action_calendar_event').read()[0]
        action['domain'] = [('room_id', '=', self.id)]
        action['views'] = [(self.env.ref('calendar.view_calendar_event_tree').id, 'tree')
                           ]
        return action


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    room_id = fields.Many2one('ebs.calendar.meeting.room', string='Room')

    @api.onchange('room_id','duration','start_datetime','stop_date')
    def room_id_onchange(self):
        for rec in self:
            if rec.room_id:
                if not rec.start and not rec.stop:
                    raise ValidationError(
                        "Please set when meeting start.")
                room_found = rec.room_id.event_ids.filtered(lambda o: (rec.start.replace(second=0) > o.start.replace(second=0) and rec.stop.replace(second=0) < o.stop.replace(second=0)) or (rec.start.replace(second=0) < o.start.replace(second=0) and rec.stop.replace(second=0) < o.stop.replace(second=0))
                                                            or (o.stop.replace(second=0) > o.start.replace(second=0) and rec.stop.replace(second=0) > rec.stop.replace(second=0)) or (rec.start.replace(second=0) < o.start.replace(second=0) and rec.stop.replace(second=0) > o.stop.replace(second=0)) or ((rec.start.replace(second=0) == o.start.replace(second=0) or rec.stop.replace(second=0) == o.stop.replace(second=0))))
                if room_found:
                    raise ValidationError(
                        "There is an already meeting schedule in this room on this time. "
                        "Please change your time or room.")
                rec.location = rec.room_id.location
            else:
                rec.location = False


