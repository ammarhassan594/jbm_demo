from odoo import fields, models, api


class DmsHrLeave(models.Model):
    _name = 'hr.leave'

    _inherit = ['hr.leave', 'dms.integration.mix']

