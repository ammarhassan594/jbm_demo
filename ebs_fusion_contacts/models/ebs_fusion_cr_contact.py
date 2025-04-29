from odoo import api, fields, models, _


class Cr_Contact(models.Model):
    _name = 'cr.contact'
    _description = "cr_po_box_no"

    cr_po_box_no = fields.Char("CR Po Box No")
    phone_no = fields.Char("Phone No")
    email = fields.Char("Email")
    partner_id = fields.Many2one('res.partner')
    designation_id = fields.Many2one('res.partner.title',string="Designation")



