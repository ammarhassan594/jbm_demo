# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class HRLeaveTypeCustom(models.Model):
    _inherit = 'hr.leave.type'

    is_unpaid = fields.Boolean('Is Unpaid')
    is_annual = fields.Boolean('Is Annual')
    is_paid = fields.Boolean('Is Paid')
    is_muslim = fields.Boolean(string="Muslim", default=False)
    is_qatari = fields.Boolean(string="Qatari", default=False)
    is_female = fields.Boolean(string="Female", default=False)
    is_permission = fields.Boolean(string="Is Permission")
    allocated_per_month = fields.Float('Allocated Per Month', default=1)

    is_haj_leave = fields.Boolean(
        string='Is Hajj Leave', default=False,
        required=False)

    is_sick_leave = fields.Boolean(
        string='Is Sick Leave', default=False,
        required=False)

    additional_element_type_id = fields.Many2one(
        comodel_name='ebspayroll.additional.element.types',
        string='Additional Element Type',
        required=False)

    validation_type = fields.Selection([
        ('no_validation', 'No Validation'),
        ('hr', 'HR Department'),
        ('manager', 'Line Manager'),
        ('both', 'Line Manager and HR Department')], default='hr', string='Validation')
