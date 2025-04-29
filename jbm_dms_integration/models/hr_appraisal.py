from odoo import fields, models, api


class DmsHrAppraisal(models.Model):
    _name = 'hr.appraisal'

    _inherit = ['hr.appraisal', 'dms.integration.mix']

