from odoo import api, fields, models, _


class res_partner_state(models.Model):
    _name = 'res.partner.state'
    _description = 'Res Partner State'
    _order = 'sequence'

    name = fields.Char("Name")
    sequence = fields.Char("Sequence")
    stages_type = fields.Selection([('contacts','Contacts'),('clients','Clients'),('suppliers','Suppliers'),('our_companies','Our Companies')],string="Type")

