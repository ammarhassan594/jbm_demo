from odoo import models, fields, api
from odoo.exceptions import ValidationError

class JbmAccount(models.Model):
    _name = 'jbm.account'
    _rec_name = 'jbm_account'

    jbm_account = fields.Char(string="Account Code", required=True)

    account_description = fields.Char(string="Name", required=True)

    def name_get(self):
        result = []
        for record in self:
            rec_name = f"{record.jbm_account} - {record.account_description}" if record.account_description else f"{record.jbm_account}"
            result.append((record.id, "%s" % rec_name))
        return result

    # @api.model
    # def _name_search(self, name='', args=None, operator='ilike', limit=100):
    #     if args is None:
    #         args = []
    #     domain = args + ['|', ('jbm_account', operator, name), ('account_description', operator, name)]
    #     return super(JbmAccount, self).search(domain, limit=limit).name_get()


    @api.constrains('jbm_account')
    def _validate_jbm_account(self):
        for rec in self:
            old_account = rec.env['jbm.account'].search(
                [('id', '!=', rec.id), ('jbm_account', '=', rec.jbm_account)])
            if old_account:
                raise ValidationError("There is already an account with the same code")