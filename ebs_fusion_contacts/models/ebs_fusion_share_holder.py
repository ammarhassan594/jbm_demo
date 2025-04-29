from odoo import api, fields, models, _


class Share_Holder(models.Model):
    _name = 'share.holder'
    _description = "shareholder_partner_id"

    partner_id = fields.Many2one('res.partner',string="Partner")
    shareholder_partner_id = fields.Many2one('res.partner',string="Name")
    percentage = fields.Float("Percentage")
    selection = fields.Selection([('local','Local'),('foregin','Foregin')],string="Type")
    shareholder_type = fields.Selection([('person', 'Individual'), ('company', 'Company')],"Shareholder Type",readonly=True)
    shareholder_doc_ids = fields.One2many('documents.document','shareholder_id',string="Documents")

    @api.onchange('shareholder_partner_id')
    def onchange_shareholder_type(self):
        self.shareholder_type = self.shareholder_partner_id.company_type

