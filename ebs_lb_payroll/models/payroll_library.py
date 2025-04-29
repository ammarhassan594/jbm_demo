# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HREmployees(models.Model):
    _inherit = 'hr.employee'

    emp_childs = fields.One2many(
        comodel_name='hr.emp.child',
        inverse_name='emp_id',
        string="Children's",
        required=False)


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'
    wage_type = fields.Selection(selection_add=[('daily', 'Daily Wage')],ondelete={'daily': 'set default'})


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    def _get_country_lebanon(self):
        return self.env['res.country'].search([('code', '=', 'QA')], limit=1).id

    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=_get_country_lebanon)
    estate_number = fields.Char(
        string='Estate Number',
        required=False)
    building = fields.Char(
        string='Building',
        required=False)
    floor = fields.Char(
        string='Floor',
        required=False)
    fax = fields.Char(
        string='Fax',
        required=False)
    area = fields.Char(
        string='Area',
        required=False)
    po_box = fields.Char(
        string='PO Box',
        required=False)
    # address_zone = fields.Char(
    #     string='National Address Zone'
    # )
    # address_street = fields.Char(
    #     string='National Address Street'
    # )
    # address_building = fields.Char(
    #     string='National Address Building'
    # )