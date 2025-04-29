from odoo import api, fields, models, _


class ebsContactResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    branch = fields.Char("Branch")
    opened_since = fields.Date("Opened Since")
    comments = fields.Text("Comments")
    furthur_instruction = fields.Text(string='Any Further Instructions',related='bank_id.furthur_instruction')
    bank_details_home_country = fields.Text(string='Bank Details in Home Country',related='bank_id.bank_details_home_country')
    client_id = fields.Many2one('res.partner')
    swift_code = fields.Char(string="Swift Code")

class ebsResBank(models.Model):
    _inherit = 'res.bank'

    furthur_instruction = fields.Text(string='Any Further Instructions')
    bank_details_home_country = fields.Text(string='Bank Details in Home Country')
