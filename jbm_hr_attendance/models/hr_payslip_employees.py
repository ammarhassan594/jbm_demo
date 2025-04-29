# -*- coding: utf-8 -*-
from odoo.tools import format_date
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

import logging

LOGGER = logging.getLogger(__name__)


class HRPayslipRunWizard(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        self.ensure_one()
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            today = fields.date.today()
            first_day = today + relativedelta(day=1)
            last_day = today + relativedelta(day=31)
            if from_date == first_day and end_date == last_day:
                batch_name = from_date.strftime('%B %Y')
            else:
                batch_name = _('From %s to %s', format_date(self.env, from_date), format_date(self.env, end_date))
            payslip_run = self.env['hr.payslip.run'].create({
                'name': batch_name,
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))
        employees = self.with_context(active_test=False).employee_ids
        if not employees:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        employees -= payslip_run.slip_ids.employee_id
        success_result = {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }
        if not employees:
            return success_result

        payslips = self.env['hr.payslip']
        Payslip = self.env['hr.payslip']

        # contracts = employees._get_contracts(
        #     payslip_run.date_start, payslip_run.date_end, states=['open','probation', 'close']
        # ).filtered(lambda c: c.active)
        contracts = self.env['hr.contract'].read_group(domain=[('employee_id', 'in', employees.ids), ('state', 'in', ['open','probation', 'close']),
                                                               ('date_start', '<=', payslip_run.cust_off_date_to),
                                                               '|',
                                                               ('date_end', '=', False),
                                                               ('date_end', '>=', payslip_run.cust_off_date_from)
                                                               ], fields=['ids:array_agg(id)', 'employee_id'],
            groupby=['employee_id'], lazy=False, orderby='date_start')

        contracts = dict((item['employee_id'][0], item['ids']) for item in contracts)
        sheet_batch_id = self.env['hr.attendance.batch'].create({
            'payslip_batch_id': payslip_run.id,
            'name': payslip_run.name,
            'date_from': payslip_run.cust_off_date_from,
            'date_to': payslip_run.cust_off_date_to,
            'actual_date_from': payslip_run.date_start,
            'actual_date_to': payslip_run.date_end,
            'employee_ids': [(6, 0, self.employee_ids.ids)],
        })
        if sheet_batch_id:
            sheet_batch_id.gen_att_sheet(contracts)

        default_values = Payslip.default_get(Payslip.fields_get())
        payslips_vals = []

        for employee_id, contract in contracts.items():
            employee_contract = sorted(contract)[-1]

            if self.env['hr.employee'].browse(int(employee_id)).contract_id.state == 'open':
                values = dict(default_values, **{
                    'name': _('New Payslip'),
                    'employee_id': int(employee_id),
                    'credit_note': payslip_run.credit_note,
                    'payslip_run_id': payslip_run.id,
                    'date_from': payslip_run.date_start,
                    'date_to': payslip_run.date_end,
                    'contract_id': int(employee_contract),
                    'struct_id': self.structure_id.id,
                })
                payslips_vals.append(values)
        payslips = Payslip.with_context(tracking_disable=True).create(payslips_vals)
        payslips._compute_name()
        payslips.compute_sheet()
        payslip_run.state = 'verify'

        return success_result


