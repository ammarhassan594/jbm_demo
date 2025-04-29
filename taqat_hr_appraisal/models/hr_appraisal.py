# -*- encoding: utf-8 -*-

from odoo import fields, models, _


class HrAppraisal(models.Model):
    _inherit = "hr.appraisal"

    hr_appraisal_warning_ids = fields.One2many('hr.appraisal.warning.line', 'hr_appraisal_id',
                                               string='Appraisal Warnings')
    hr_appraisal_description_ids = fields.One2many('hr.appraisal.description.line',
                                                   'hr_appraisal_id',
                                                   string='Appraisal Descriptions')
    hr_appraisal_note_ids = fields.One2many('hr.appraisal.note.line',
                                            'hr_appraisal_id',
                                            string='Appraisal Note')
    description = fields.Text(string="Description")
