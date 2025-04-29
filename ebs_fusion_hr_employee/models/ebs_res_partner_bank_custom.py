from odoo import api, fields, models, _


class ebsResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    employee_id = fields.Many2one('hr.employee')
    iban_no = fields.Char("IBAN No")
