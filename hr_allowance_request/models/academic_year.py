from odoo import models, fields, api, _
from datetime import datetime,date


class AcademicYear(models.Model):
    _name = 'academic.year'

    name = fields.Char(strifg='Name', required=True)
    
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='END Date', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Academic Year Name must be unique !'),
    ]
