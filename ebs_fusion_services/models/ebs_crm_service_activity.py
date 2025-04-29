from odoo import api, fields, models, _


class EbsCrmServiceActivity(models.Model):
    _name = 'ebs.crm.service.activity'
    _description = 'EBS CRM Service Activity'

    name = fields.Char("Name")
    in_documents = fields.Many2many('ebs.document.type', relation="document_in_activity", column1="activity", column2="document", string="Required In Documents")
    out_documents = fields.Many2many('ebs.document.type', relation="document_out_activity", column1="activity", column2="document", string="Required Out Documents")
    stage_id = fields.Many2one('ebs.crm.service.stage', string="Stage")
