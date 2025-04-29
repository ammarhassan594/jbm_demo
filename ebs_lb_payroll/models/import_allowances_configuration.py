# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class ImportAllowancesConfiguration(models.Model):
    _name = 'ebspayroll.import.allowances.conf'
    _description = 'Import Allowances Configuration'
    _rec_name ='name'
    name = fields.Char('Name')
    lines = fields.One2many('ebspayroll.import.allowances.conf.lines','conf_id')

class ImportAllowancesConfigurationLines(models.Model):
    _name = 'ebspayroll.import.allowances.conf.lines'
    _description = 'Import Allowances Configuration'

    conf_id = fields.Many2one('ebspayroll.import.allowances.conf')
    label = fields.Char('Label')
    template = fields.Selection([('comment', 'Comment'),
                                 ('no_working_days', 'Number Of Working Days'),
                                 ('additional_element_type', 'Additional Element Type')], string="Template")
    additional_type = fields.Many2one('ebspayroll.additional.element.types',string="Additional Type")




