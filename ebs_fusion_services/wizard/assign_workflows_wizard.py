from odoo import fields, models


class AssignWorkflowsWizard(models.TransientModel):
    _name = "assign.workflows.wizard"
    _description = "Assign Workflows Wizard"

    user_id = fields.Many2one(comodel_name='res.users', string='User', required=1, domain="[('share','=',False)]")
    workflow_ids = fields.Many2many(comodel_name='ebs.crm.proposal.workflow.line', string='Workflows')

    def confirm_button(self):

        for workflow_id in self.workflow_ids.filtered(lambda o: o.status == 'draft'):
            workflow_id.write({'assigned_to': self.user_id.id})
