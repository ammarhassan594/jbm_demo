from odoo import fields, models, _, api
from datetime import date,datetime

class EbsBatchServiceOrder(models.Model):
    _name = 'ebs.batch.service.order'
    _description = 'EBS Batch Service Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=1)
    service_id = fields.Many2one('ebs.crm.service','Service')
    company_id = fields.Many2one('res.company', 'Company', required=1, default=lambda self: self.env.company)
    date = fields.Date(default=date.today(), string='Date', required=1)
    target_audience = fields.Selection([('employee', 'Employee')], default='employee', string='Target Audience', readonly=1)
    client_id = fields.Many2one('res.partner', 'Client', required=1)
    employee_ids = fields.Many2many('hr.employee', string='Employees', required=1)
    status = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')],string='Status', default='draft')
    option_id = fields.Many2one('ebs.service.option', string="Option")
    assigned_user_id = fields.Many2one(comodel_name='res.users', string='Responsible User',
                                       default=lambda self: self.env.user,
                                       domain="[('share','=',False)]")
    service_order_count = fields.Integer('Service Order Count', compute='_compute_service_order_count')

    def confirm_batch_order(self):
        for employee in self.employee_ids:
            service_order_id = self.env['ebs.crm.service.process'].create({
                'service_id': self.service_id.id or False,
                'company_id': self.company_id.id,
                'service_order_type': 'employee',
                'client_id': self.client_id.id,
                'partner_id': employee.user_partner_id.id,
                'employee_id': employee.id,
                'option_id': self.option_id.id or False,
                'assigned_user_id': self.assigned_user_id.id,
                'service_order_date': self.date,
                'batch_order_id': self.id,
            })
            service_order_id.fetch_workflows()
        self.status = 'confirm'

    def _compute_service_order_count(self):
        ServiceOrder = self.env['ebs.crm.service.process']
        for rec in self:
            rec.service_order_count = ServiceOrder.search_count([('batch_order_id', '=', rec.id)]) or 0

    def action_created_service_orders(self):
        self.ensure_one()
        service_orders = self.env['ebs.crm.service.process'].sudo().search([('batch_order_id', '=', self.id)])
        action = self.env.ref('ebs_fusion_services.ebs_fusion_crm_proposal_process_action').read()[0]
        action["context"] = {"create": False}
        if len(service_orders) > 1:
            action['domain'] = [('id', 'in', service_orders.ids)]
        elif len(service_orders) == 1:
            action['views'] = [(self.env.ref('ebs_fusion_services.view_ebs_crm_service_process_form').id, 'form')]
            action['res_id'] = service_orders.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


