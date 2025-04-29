from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_proposal_ids = fields.One2many('ebs.crm.proposal', 'contact_id', String="CRM Proposal",
                                           context={'active_test': False})

    service_order_ids = fields.One2many('ebs.crm.service.process', 'client_id',string='Service Order')
    labor_quota_ids = fields.One2many('ebs.labor.quota', 'partner_id', string='Labor Quota')

    def open_proposals(self):
        self.ensure_one()
        action = self.env.ref('ebs_fusion_services.action_ebs_crm_proposal').read()[0]
        action['context'] = {
            'default_contact_id': self.id,
        }
        return action

    def open_service_orders(self):
        self.ensure_one()
        action = self.env.ref('ebs_fusion_services.ebs_fusion_crm_proposal_process_action').read()[0]
        action['context'] = {
            'default_partner_id': self.id,
        }
        return action
