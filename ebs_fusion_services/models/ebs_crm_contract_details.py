from odoo import api, fields, models, _

class ebsCrmContractDetails(models.Model):
    _name = 'ebs.crm.contract.details'
    _description = 'EBS CRM Contract Details'

    name = fields.Char('Name')
    parent_id = fields.Many2one('ebs.crm.contract.details','Parent', domain="[('id', '!=',id),('parent_id','!=',id)]")
    company_ids = fields.Many2many('res.company',string='Company')
    fos = fields.Boolean('FOS')
    fme = fields.Boolean('FME')
    fss = fields.Boolean('FSS')

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        for rec in self:
            if rec.parent_id:
                rec.fos = rec.parent_id.fos
                rec.fme = rec.parent_id.fme
                rec.fss = rec.parent_id.fss
            else:
                rec.fos = False
                rec.fme = False
                rec.fss = False
