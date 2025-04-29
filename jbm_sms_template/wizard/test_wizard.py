from odoo import models, fields, api


class TestWizard(models.TransientModel):

    _name = 'jbm.sms.test.wizard'

    employee_id = fields.Many2one('hr.employee')

    def test_wizard_fun(self):
        pass
