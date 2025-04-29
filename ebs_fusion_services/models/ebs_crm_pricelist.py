from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class ebsCrmPricelist(models.Model):
    _name = 'ebs.crm.pricelist'
    _description = 'EBS Pricelist'

    name = fields.Char('Name')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    company_id = fields.Many2one('res.company',string='Company',required=1,default=lambda self: self.env.company)
    type = fields.Selection([('individual','Individual'),('company','Company')])
    pricelist_line_ids = fields.One2many('ebs.crm.pricelist.line','pricelist_id','Pricelist Lines',copy=True)
    active = fields.Boolean(string='Active')

    _sql_constraints = [
        ('name_unique', 'unique (name)', "A pricelist with this name already exists"),
    ]

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = default or {}
        default['name'] = self.name + 'Copy'

        return super(ebsCrmPricelist, self).copy(default=default)


class ebsCrmPricelistLines(models.Model):
    _name = 'ebs.crm.pricelist.line'
    _description = 'EBS CRM Pricelist Line'

    def default_company(self):
        return self.pricelist_id.company_id.id or ''

    name = fields.Char('Name')
    pricelist_id = fields.Many2one('ebs.crm.pricelist','Pricelist')
    pricelist_category_id = fields.Many2one('ebs.crm.pricelist.category','Category')
    service_ids = fields.Many2many('ebs.crm.service',string='Services')
    authority_id = fields.Many2one(related='service_ids.authority_id',string='Authority')
    company_id = fields.Many2one(related='pricelist_id.company_id')
    govt_product_id = fields.Many2one('product.template',string='Govt. Product')
    fusion_product_id = fields.Many2one('product.template', string='Fusion Product')
    govt_fees = fields.Float(string='Govt. Fees')
    fusion_fees = fields.Float(string='Main Company Fees')
    govt_urgent_fees = fields.Float(string='Govt. Urgent Fees')
    fusion_urgent_fees = fields.Float(string='Fusion Urgent Fees')
    comments = fields.Text('Comments')
    show_in_portal = fields.Boolean('Show in Portal',default=True)
    is_included = fields.Boolean()

    @api.onchange('govt_product_id')
    def onchange_govt_product_id(self):
        for rec in self:
            if rec.govt_product_id.list_price:
                rec.govt_fees = rec.govt_product_id.list_price
                rec.govt_urgent_fees = rec.govt_product_id.list_price

    @api.onchange('fusion_product_id')
    def onchange_fusion_product_id(self):
        for rec in self:
            if rec.fusion_product_id.list_price:
                rec.fusion_fees = rec.fusion_product_id.list_price
                rec.fusion_urgent_fees = rec.fusion_product_id.list_price
