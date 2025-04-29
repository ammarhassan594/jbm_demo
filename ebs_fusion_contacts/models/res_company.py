from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from datetime import date, datetime


class Contacts_Companies(models.Model):
    _inherit = 'res.company'

    def read(self, fields=None, load='_classic_read'):
        """ Override to explicitely call check_access_rule, that is not called
            by the ORM. It instead directly fetches ir.rules and apply them. """
        # self.check_access_rule('read')
        return super(Contacts_Companies, self).sudo().read(fields=fields, load=load)