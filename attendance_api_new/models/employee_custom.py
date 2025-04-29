from odoo import models, fields, api, _


class HrEmployeeInherited(models.Model):
    _inherit = 'hr.employee'

    employee_qid_number = fields.Char("QID Number",store=True)

    # def _qid_exp_date_compute(self):
    #     for rec in self:
    #         res = super(HrEmployeeInherited, rec)._qid_exp_date_compute()
    #         rec.employee_qid_number = rec.qid_no if rec.qid_no else False
    #     return res
