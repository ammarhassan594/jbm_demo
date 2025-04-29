# -*- coding: utf-8 -*-
from odoo import fields, models, api


class AppraisalResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    activate_skills_appraisal = fields.Boolean("Activate Skills",
                                               config_parameter="jbm_hr_appraisal.activate_skills_appraisal")
    appraisal_stamp_width = fields.Float(string="Stamp Width (cm)",
                                        config_parameter='jbm_hr_appraisal.appraisal_stamp_width')

    appraisal_stamp_height = fields.Float(string="Stamp Height (cm)",
                                         config_parameter='jbm_hr_appraisal.appraisal_stamp_height')

    appraisal_signature_width = fields.Float(string="Signature width (cm)",
                                            config_parameter='jbm_hr_appraisal.appraisal_signature_width')

    appraisal_signature_height = fields.Float(string="Signature height (cm)",
                                             config_parameter='jbm_hr_appraisal.appraisal_signature_height')