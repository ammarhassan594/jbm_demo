from odoo import models, fields, api


class InheritResourceCalendar(models.Model):

    _inherit = 'resource.calendar'

    reference_violation = fields.Float()
