# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RecruitmentStage(models.Model):
    _inherit = "hr.recruitment.stage"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_approve', 'Under Approve'),
        ('approved', 'Approved')
    ], default='draft')


class Applicant(models.Model):
    _name = 'hr.applicant'
    _inherit = ['hr.applicant', 'dynamic.approval.mixin']
    _state_field = "state"
    _state_from = ['under_approve']
    _state_to = ['approved']

    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_approve', 'Under Approve'),
        ('approved', 'Approved')
    ], default='draft', compute="_compute_application_state", store=True)

    @api.depends('stage_id', 'stage_id.state')
    def _compute_application_state(self):
        for rec in self:
            if rec.stage_id:
                rec.state = rec.stage_id.state

    def _action_final_approve(self):
        res = super()._action_final_approve()
        if self._name == 'hr.applicant':
            approved_stage = self.env['hr.recruitment.stage'].search([('state', '=', 'approved')], limit=1)
            if approved_stage:
                self.stage_id = approved_stage
        return res
