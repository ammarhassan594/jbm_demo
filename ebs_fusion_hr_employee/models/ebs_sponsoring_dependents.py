from odoo import api, fields, models, _


class EbsSponsoringDependents(models.Model):
    _name = 'ebs.sponsoring.dependents'
    _description = 'EBS Sponsoring Dependents'
    _rec_name = 'marriage_certificate_id'

    employee_id = fields.Many2one('hr.employee')
    dependant_type = fields.Selection([('wife', 'Wife'), ('child', 'Child')], string='Dependant Type', default='wife')
    marriage_certificate_id = fields.Many2one('documents.document', string="Marriage Certificate")
    marriage_contract_id = fields.Many2one('documents.document', string="Marriage Contract")
    non_marriageid_certificate_id = fields.Many2one('documents.document', string="Non-Marriage Certificate")
    divorce_certificate_id = fields.Many2one('documents.document', string="Divorce certificate")
    birth_certificate_id = fields.Many2one('documents.document', string="Birth Certificate")
    lives_birth_id = fields.Many2one('documents.document', string="Notification of Live Birth")
    bank_info = fields.Char("Bank Information")
    bank_name = fields.Char("Bank Name")
    iban = fields.Char("IBAN")
    # BranchAdress
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    text = fields.Text("Others/Comments")
