# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from odoo.osv import expression


class HrLeaveTypeCustom(models.Model):
    _inherit = "hr.leave.type"

    add_validation_past_leave = fields.Boolean(string="Add validation past leave")
