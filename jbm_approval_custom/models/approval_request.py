from odoo import models, fields, api, _

class  InheritApprovalRequest(models.Model):
    _inherit = 'approval.request'


    invoice_id = fields.Many2one("account.move", compute="_get_bill", store=False)
    accountant_id = fields.Many2one("res.users")
    can_create_bill = fields.Boolean(string="Create Bill", related="category_id.create_bill")

    def create_bill(self):
        self.ensure_one()
        domain = [('res_model', '=', 'approval.request'), ('res_id', 'in', self.ids)]
        attachment_data = self.env['ir.attachment'].search(domain)

        attachment_vals = []
        if attachment_data:
            for attachment in attachment_data:
                attachment_vals.append((0, 0, {
                    'name': attachment.name,
                    'datas': attachment.datas,
                    'res_model': 'account.move',
                }))
        return  {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": 'form',
            "target": 'current',
            "context": {
                'form_view_initial_mode': 'edit',
                'default_move_type': 'in_invoice',
                'default_date': self.date,
                'default_invoice_date': self.date,
                'default_partner_id': self.create_uid.partner_id.id,
                'default_approval_request_id': self.id,
                'default_attachment_ids': attachment_vals if attachment_vals else None

            },
        }


    def _get_bill(self):
        self.ensure_one()
        self.invoice_id = self.env['account.move'].sudo().search([
            ('approval_request_id', '=', self.id),
        ], limit=1).id
        if self.request_status == 'new':
            self.accountant_id = self.invoice_id.create_uid.id

