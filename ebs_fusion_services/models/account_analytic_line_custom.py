# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    timesheet_workflow_id = fields.Many2one('ebs.crm.proposal.workflow.line', string='Workflow Line')
    service_process_id = fields.Many2one('ebs.crm.service.process', 'Service Order', store=True)

    @api.model
    def create(self, vals):
        res = super(AccountAnalyticLine, self).create(vals)
        if res.timesheet_workflow_id:
            service_process_id = res.timesheet_workflow_id.service_process_id
            res.write({
                'service_process_id': service_process_id.id,
            })
        return res
