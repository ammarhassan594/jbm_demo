from odoo import api, fields, models, _


class ebsCaseContact(models.Model):
    _name = 'ebs.case.contact'
    _description = 'EBS Case Contact'

    name = fields.Char(string="Name")
    case_id = fields.Many2one('ebs.legal.case')
    partner_id = fields.Many2one('res.partner', string="Contact")
    related_number = fields.Char('Related Number')
    type = fields.Selection([('accuser', 'Accuser'), ('defender', 'Defender')])

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            if rec.partner_id:
                rec.name = rec.partner_id.name
            else:
                rec.name = ''
