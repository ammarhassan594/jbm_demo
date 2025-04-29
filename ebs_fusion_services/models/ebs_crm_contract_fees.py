from odoo import api, fields, models, _

class ebsCrmContractFees(models.Model):
    _name = 'ebs.crm.contract.fees'
    _description = 'EBS CRM Contract Fees'

    name = fields.Char('Name')
    product_id = fields.Many2one('product.template','Product')

    amount = fields.Float(string='Amount')
    fme = fields.Boolean('FME')
    fss = fields.Boolean('FSS')
    one_time = fields.Boolean()


    @api.onchange('product_id')
    def onchange_product(self):
        for rec in self:
            if rec.product_id:
                rec.amount = rec.product_id.list_price

