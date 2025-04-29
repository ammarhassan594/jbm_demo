from odoo import models, fields, api


class EbsJbmWaqf(models.Model):
    _name = 'ebs.jbm.waqf'
    _description = 'Jbm employee Waqf screen'

    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], string="Status", default="draft")
    country_id = fields.Many2one(comodel_name="res.country", string="Country")
    address = fields.Text(string="Address")
    date = fields.Date(string="Date")
    attachment_ids = fields.Many2many(comodel_name='ir.attachment', string="Attachments")
    type = fields.Char(string="Type")
    in_conflict = fields.Boolean(string="In_conflict")
    size = fields.Char(string="Size")
    owner_id = fields.Many2one(comodel_name='res.users', string="Owner", default=lambda self: self.env.user)
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    amount = fields.Monetary(string="Amount")
    year = fields.Integer(string="Year")
    geolocation = fields.Char(string="Geolocation")
    property_manager = fields.Many2one(comodel_name="res.partner", string="Property Manager")
    opening_date = fields.Date(string="Opening Date")
    conflict_reason = fields.Char(string="Conflict Reason")
    sequence = fields.Integer(string="Sequence")
    parent_id = fields.Many2one(comodel_name="ebs.jbm.waqf", string="Parent Waqf")
