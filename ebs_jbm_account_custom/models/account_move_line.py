from odoo import models, fields, api, _


class InheritAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    legacy_baned_value = fields.Char(string="Legacy Baned")
    legacy_job_value = fields.Char(string="Legacy Job")
    legacy_department_value = fields.Char(string="Legacy Department")
    legacy_hr_value = fields.Char(string="Legacy HR Value")
    legacy_amount_USD = fields.Char(string="Legacy Amount USD")
    legacy_currency = fields.Char(string="Legacy Currency")
