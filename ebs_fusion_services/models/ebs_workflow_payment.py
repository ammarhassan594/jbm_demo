from odoo import api, fields, models, _


class ebsWorkflowPayment(models.Model):
    _name = 'ebs.workflow.payment'
    _description = 'EBS Workflow Payment'

    workflow_id = fields.Many2one(comodel_name='ebs.crm.proposal.workflow.line')
    product_id = fields.Many2one(comodel_name='product.product', string='Payment For')
    credit_card_id = fields.Many2one(comodel_name='ebs.accounts.credit.cards', string='Credit Card')
    date = fields.Date(string='Date')
    amount = fields.Float(string='Amount')
    move_id = fields.Many2one(comodel_name='account.move', string='Journal Entry')
    service_order_id = fields.Many2one('ebs.crm.service.process', 'Service Order')
    file_to_payment = fields.Binary(string='Receipt', required=True)
    is_invoiced = fields.Boolean('Is Invoiced')