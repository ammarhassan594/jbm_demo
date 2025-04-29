# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ContactCustom(models.Model):
    _inherit = 'res.partner'

    classification = fields.Many2one('contact.classification', string="Classification")
