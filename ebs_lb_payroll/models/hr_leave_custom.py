# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from datetime import date


class HRLeaveCustom(models.Model):
    _name = 'hr.leave'
    _inherit = ['hr.leave', 'dynamic.approval.mixin']
    _state_from = ['confirm', 'refuse']
    _state_to = ['validate']


    is_annual = fields.Boolean(string="Is Annual", default=False, related='holiday_status_id.is_annual')
    is_unpaid = fields.Boolean(string="Is Unpaid", default=False, related='holiday_status_id.is_unpaid')
    is_muslim = fields.Boolean(string="Hajj", default=False, compute='compute_is_muslim')


    @api.onchange('employee_id', 'employee_id.religion')
    def compute_is_muslim(self):
        if self.employee_id.religion == 'muslim':
            self.is_muslim = True
        else:
            self.is_muslim = False

    @api.model
    def create(self, vals):
        leave = super(HRLeaveCustom, self).create(vals)
        for rec in leave:
            if rec.holiday_status_id.is_haj_leave:
                start_date = date(rec.date_from.year, 1, 1)
                end_date = date(rec.date_from.year, 12, 31)
                leave_list = self.env['hr.leave'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('holiday_status_id', '=', rec.holiday_status_id.id),
                    ('date_from', '>=', start_date),
                    ('date_from', '<=', end_date),
                    ('state', '=', 'validate')
                ])
                if len(leave_list) > 0:
                    raise ValidationError(_("Cannot take 2 Haj Leave per year"))
        return leave
