# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ContactClassification(models.Model):
    _name = 'contact.classification'

    name = fields.Char(string="Name")

