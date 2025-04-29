# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class CreateAssetFromPO(models.TransientModel):
    _name = 'ebs.transfer.asset'
    _description = 'Create Asset From PO wizard'

    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset',
        required=False)
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True)
    date = fields.Date(
        string='Date', default=datetime.today().date(),
        required=True)

    def transfer_asset(self):
        self.asset_id.employee_id = self.employee_id.id
        self.env['ebs.asset.transfer.log'].create({
            'transfer_date': self.date,
            'asset_id': self.asset_id.id,
            'employee_id': self.employee_id.id
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
