from odoo import api, fields, models, _


class Res_Partner(models.Model):
    _inherit = 'res.partner'

    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
                                                     string="Account Receivable",
                                                     domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
                                                     help="This account will be used instead of the default one as the receivable account for the current partner",
                                                     required=False)

    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
                                                  string="Account Payable",
                                                  domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
                                                  help="This account will be used instead of the default one as the payable account for the current partner",
                                                  required=False,)

    # conversion_rate_ids = fields.One2many('ebs.client.conversion.rate', 'partner_id', string='Custom conversion Rate')





class AgedRecieable(models.AbstractModel):
    _inherit = 'account.aged.receivable'

    def _set_context(self, options):
        ctx = super(AgedRecieable, self)._set_context(options)
        if ctx.get('button') == 'True':
            ctx['partner_ids'] = self.env['res.partner'].browse(self.env.context.get('active_id'))
        ctx['account_type'] = 'receivable'
        return ctx


class AgedPayable(models.AbstractModel):
    _inherit = 'account.aged.payable'

    def _set_context(self, options):
        ctx = super(AgedPayable, self)._set_context(options)
        if ctx.get('button') == 'True':
            ctx['partner_ids'] = self.env['res.partner'].browse(self.env.context.get('active_id'))
        ctx['account_type'] = 'payable'
        ctx['aged_balance'] = True
        return ctx
