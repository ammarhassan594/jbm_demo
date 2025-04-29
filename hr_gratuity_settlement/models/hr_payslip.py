from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta


class HRPayslipIn(models.Model):
    _inherit = 'hr.payslip'

    gratuity_id = fields.Many2one(comodel_name="hr.gratuity", string="Gratuity ID", required=False)
    has_gratuity = fields.Boolean(default=False)
    actual_day_from = fields.Date(string="Actual Day From", readonly=True)
    actual_day_to = fields.Date(string="Actual Day To", readonly=True)
    remarks = fields.Text(string="Remarks", required=False, )

    @api.onchange('gratuity_id')
    def onchange_gratuity_id(self):
        for rec in self:
            if rec.gratuity_id:
                rec.has_gratuity = True

    def action_payslip_done(self):
        payslip = super(HRPayslipIn, self).action_payslip_done()
        # self._create_deduction_ele()
        return payslip

    # def _create_deduction_ele(self):
    #     for rec in self:
    #         if rec.state == 'done':
    #             for line in rec.line_ids:
    #                 if line.code == 'SADJ':
    #                     if line.amount:
    #                         month = rec.date_from.month
    #                         year = rec.date_from.year
    #                         if month == 12:
    #                             month = 0
    #                             year = year + 1
    #                         next_month = rec.date_from.replace(year=year, month=month + 1, day=1)
    #                         ded_typ = rec.env['ebspayroll.additional.element.types'].search([('code', '=', 'AD')])
    #                         # ded_element = rec.env['ebspayroll.additional.elements'].search([('type', '=', ded_typ.id),
    #                         #                                                                 ('payment_date', '>=',
    #                         #                                                                  next_month),
    #                         #                                                                 ('payment_date', '<=',
    #                         #                                                                  next_month)])
    #                         lines = [(0, 0, {
    #                             'employee': rec.employee_id.id,
    #                             'amount': line.amount
    #                         })]
    #                         # if ded_element:
    #                         #     ded_element.write({'lines': lines})
    #
    #                         ded_element = rec.env['ebspayroll.additional.elements'].create(
    #                             {
    #                                 'type': ded_typ.id,
    #                                 'rule_type': 'D',
    #                                 'payment_date': next_month,
    #                                 'lines': lines
    #                             }
    #                         )
