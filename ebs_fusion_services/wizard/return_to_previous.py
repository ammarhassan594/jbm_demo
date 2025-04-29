from odoo import models, fields, api, _

class ReturntoPreviousWizard(models.TransientModel):
    _name = 'ebs.return.to.previous.wizard'
    _description = 'Return to Previous Wizard'

    return_reason = fields.Text('Reason')

    def confirm_button(self):
        workflow_id = self.env['ebs.crm.proposal.workflow.line'].browse([self.env.context.get('active_id')])
        workflow_id.status = 'ongoing'
        for workflow in workflow_id.dependant_workflow_ids:
            workflow.return_reason = self.return_reason
            workflow.status = 'returned'
            notification_ids = []
            recipient_ids = []
            if workflow.assigned_to:
                notification_ids.append((0, 0, {
                    'res_partner_id': workflow_id.assigned_to.partner_id.id,
                    'notification_type': 'inbox'}))
                recipient_ids.append((4, workflow.assigned_to.partner_id.id))

            workflow.message_post(
                body='The workflow %s of service order %s has been returned. Please check the workflow for the return reason' % (
                    workflow.name, workflow.service_process_id.name),
                message_type='notification',
                subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id,
                notification_ids=notification_ids)
            mail_server_id = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
            mail = self.env['mail.mail'].sudo().create({
                'body_html': '<p>The workflow %s of service order %s has been returned. Please check the workflow for the return reason.</p>'
                             % (workflow.name, workflow.service_process_id.name),
                'subject': 'Workflow Returned',
                'recipient_ids': recipient_ids,
                'mail_server_id': mail_server_id and mail_server_id.id,
            })
            mail.send()