# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _name = "ebs.asset.transfer.log"
    _description = "Asset Transfer Log"
    _order = "transfer_date"

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=False)

    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset',
        required=False)

    transfer_date = fields.Date(
        string='Date',
        required=False)



