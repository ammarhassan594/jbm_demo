from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # proposal_report_action_id = fields.Many2one('ir.actions.report', string="Proposal Report Action", default=lambda self: self.env.ref('ebs_fusion_crm.action_proposal_report1'))
    proposal_report_action_id = fields.Many2one('ir.actions.report', string="Proposal Report Action")
    proposal_email_temp_id = fields.Many2one('mail.template', string="Proposal Email Template")
    # proposal_email_temp_id = fields.Many2one('mail.template', string="Proposal Email Template", default=lambda self: self.env.ref('ebs_fusion_crm.mail_template_stage_proposal_lead'))


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        proposal_report_action_id = params.get_param('proposal_report_action_id', default=False)
        proposal_email_temp_id = params.get_param('proposal_email_temp_id', default=False)
        res.update(
            proposal_report_action_id=int(proposal_report_action_id),
            proposal_email_temp_id=int(proposal_email_temp_id),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("proposal_report_action_id", self.proposal_report_action_id.id)
        self.env['ir.config_parameter'].sudo().set_param("proposal_email_temp_id", self.proposal_email_temp_id.id)
