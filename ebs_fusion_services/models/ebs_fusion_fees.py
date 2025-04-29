from odoo import api, fields, models, _

class ebsFusionFees(models.Model):
    _name = 'ebs.fusion.fees'
    _description = 'EBS Fusion Fees'
    _rec_name = 'name'

    name = fields.Char('Name')
    is_fme = fields.Boolean('FME')
    is_fss = fields.Boolean('FSS')
    is_fos = fields.Boolean('FOS')
    code = fields.Char('Code')
    type = fields.Selection([('normal','Normal'),('differed_income','Differed Income'), ('proforma', 'Proforma')],string='Type')
    product_id = fields.Many2one('product.template', string='Product')
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    invoice_period = fields.Selection([('onetime', 'One Time'), ('monthly', 'Monthly'), ('yearly', 'Yearly')], string="Invoice Period", default='onetime')


