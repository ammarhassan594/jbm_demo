# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import datetime


class HrAppraisalNoteLine(models.Model):
    _name = 'hr.appraisal.note.line'
    _description = 'Hr Appraisal Note Line'

    hr_appraisal_id = fields.Many2one('hr.appraisal', string="Employee Appraisal")
    hr_notes = fields.Char(string="HR Notes")
    score = fields.Char(string="Score")
    training_date = fields.Date("Training Date")
    training_time = fields.Char("Training Time")
    training_place = fields.Char("Training Place")
    training_course = fields.Char("Training Course")

    training_name = fields.Char("Training Name")
    appraisal_description = fields.Char("Appraisal Description")
    description = fields.Char("Description")
    subject = fields.Char("Subject")
