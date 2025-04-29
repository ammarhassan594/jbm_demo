# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PayrollHrSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    overtime_cutoff_day = fields.Integer(string="Overtime CutOff Day")

    def set_values(self):
        result = super(PayrollHrSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('ohrms_overtime.overtime_cutoff_day', self.overtime_cutoff_day)
        return result

    @api.model
    def get_values(self):
        result = super(PayrollHrSettings, self).get_values()
        overtime_day = int(self.env['ir.config_parameter'].sudo().get_param('ohrms_overtime.overtime_cutoff_day'))
        # ooredoo_temp = int(self.env['ir.config_parameter'].sudo().get_param('ebs_lb_payroll.ooredoo_template'))
        result.update(
            overtime_cutoff_day=overtime_day,
        )
        return result
