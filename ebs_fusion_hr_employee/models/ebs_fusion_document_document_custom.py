from odoo import api, fields, models, _


class DocumentsCustom(models.Model):
    _inherit = 'documents.document'

    employee_client_id = fields.Many2one(comodel_name='res.partner',
                                         related='employee_id.partner_parent_id',
                                         string="Employee Client")
    employee_type = fields.Selection(related='employee_id.employee_type', string='Employee Type')

    @api.model
    def create(self, vals):
        res = super(DocumentsCustom, self).create(vals)
        if res.partner_id:
            res.employee_id = res.partner_id.related_employee_id
        if res.employee_id:
            res.partner_id = res.employee_id.user_partner_id
        return res
