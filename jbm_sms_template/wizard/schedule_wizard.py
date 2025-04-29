from odoo import models, fields, api


class ScheduleWizard(models.TransientModel):

    _name = 'jbm.sms.schedule.wizard'

    date = fields.Date()

    def schedule_fun(self):
        pass
