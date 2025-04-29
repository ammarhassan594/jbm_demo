from odoo import models, fields, api, _
import requests
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SendSMSSchedule(models.TransientModel):
    _name = 'send.sms.schedule'

    schedule_date = fields.Datetime(string='Schedule Date', required=True)
    send_sms_id = fields.Many2one('send.sms', string='Send SMS', required=True, ondelete='cascade')

    def action_schedule(self):
        if self.send_sms_id:
            self.send_sms_id.schedule_date = self.schedule_date
            self.send_sms_id.state = 'in_queue'


