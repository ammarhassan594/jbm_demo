from odoo import api, fields, models, _


class Company_Managment_Structure(models.Model):
    _name = 'company.managment.structure'
    _description = "name"

    partner_id = fields.Many2one('res.partner', "Name")
    compan_mgt_position_id = fields.Many2one('company.mgt.structure.position', "Position")
    type = fields.Selection(
        [('bod', 'BOD'), ('gm', 'GM')], string='Type')
    name = fields.Char("Name")
    email = fields.Char("Email")
    mobile = fields.Char("Mobile")
    extension = fields.Char("Extension")
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')


class Company_position(models.Model):
    _name = 'company.mgt.structure.position'
    _description = "name"

    name = fields.Char("Name")
