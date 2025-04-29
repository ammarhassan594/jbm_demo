from odoo import fields, models

from odoo.exceptions import UserError, ValidationError

class WorkflowChangeStatusWizard(models.TransientModel):
    _name = "ebs.wf.status.wiz"
    _description = "Change Status Wiz"

    status = fields.Selection(
        [('draft', 'Draft'), ('ongoing', 'Ongoing'), ('onhold', 'Onhold'), ('completed', 'Completed'),
         ('returned', 'Returned'), ('cancelled', 'Cancelled')],string='Status')
    workflow_ids = fields.Many2many(comodel_name='ebs.crm.proposal.workflow.line', string='Workflows')

    def confirm_button(self):
        for workflow_id in self.workflow_ids:
            if workflow_id.status == 'completed':
                raise UserError("Workflow must not be completed to change status.")
            workflow_id.write({'status': self.status})
