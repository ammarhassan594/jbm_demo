# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HRDepartment(models.Model):
    _inherit = 'hr.department'

    directorate = fields.Many2one(comodel_name="hr.department", compute="_compute_directorate")
    is_directorate = fields.Boolean(default=False)
    line_manager_id = fields.Many2one('hr.employee', string='Line Manager 2',
                                      domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    arabic_name = fields.Char("Arabic Name")

    @api.onchange('parent_id')
    def _compute_directorate(self):
        for rec in self:
            rec.directorate = False
            # if rec.is_directorate:
            #     return False
            if rec.parent_id:
                if rec.parent_id.is_directorate:
                    rec.directorate = rec.parent_id
                elif rec.is_directorate:
                    rec.directorate = rec.id
                else:
                    rec.directorate = rec.parent_id.directorate
