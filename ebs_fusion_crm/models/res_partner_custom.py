from odoo import api, fields, models, _


class Res_Partner(models.Model):
    _inherit = 'res.partner'

    is_deliver_partner = fields.Boolean("Deliver Partner")
    is_subject_matter_expert = fields.Boolean("Subject Matter Expert")
    hubspot_id = fields.Char("Hubspot ID")
    contact_industry_ids = fields.One2many('ebs.contact.industries', 'partner_id', string="Conatct Industries")
    target_client_ids = fields.Many2many(comodel_name='res.partner',relation='target_client',column1='target_client_ids',string="Target Client")
    opportunity_ids = fields.One2many('crm.lead', 'partner_id', string='Opportunities',
                                      domain=['&',('type', '=', 'opportunity'),('tender_type', '=', 'deal')])

    def _compute_opportunity_count(self):
        all_partners = self.with_context(active_test=False).search(
            [('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        opportunity_data = self.env['crm.lead'].with_context(active_test=False).read_group(
            domain=[('partner_id', 'in', all_partners.ids), ('tender_type', '=', 'deal')],
            fields=['partner_id'], groupby=['partner_id']
        )

        self.opportunity_count = 0
        for group in opportunity_data:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.opportunity_count += group['partner_id_count']
                partner = partner.parent_id


    @api.model
    def default_get(self, fields):
        vals = super(Res_Partner,self).default_get(fields)
        industries = []
        for industry in self.env['res.partner.industry'].search([('parent_id', '=', False)]):
            industries.append((0, 0, {
                'industry_id': industry.id,
            }))
        vals['contact_industry_ids'] = industries

        return vals

    def _compute_ticket_count(self):
        if self.company_partner == True:
            self.ticket_count = 0
            ticket_count = self.env['helpdesk.ticket'].search_count([('company_id', '=', self.company_id.id)])
            self.ticket_count = ticket_count

        else:
            # retrieve all children partners and prefetch 'parent_id' on them
            all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
            all_partners.read(['parent_id'])

            # group tickets by partner, and account for each partner in self
            groups = self.env['helpdesk.ticket'].read_group(
                [('partner_id', 'in', all_partners.ids)],
                fields=['partner_id'], groupby=['partner_id'],
            )
            self.ticket_count = 0
            for group in groups:
                partner = self.browse(group['partner_id'][0])
                while partner:
                    if partner in self:
                        partner.ticket_count += group['partner_id_count']
                    partner = partner.parent_id


