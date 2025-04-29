import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, tools, api, exceptions, _
from odoo.tools.misc import format_date
from odoo.exceptions import ValidationError


class AttendanceBatch(models.Model):
    _name = 'hr.attendance.batch'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="employee_shift_att_batch_rel",
        column1="batch_id",
        column2="employee_id",
        string="Employees",
    )

    date_from = fields.Date(string="From", required=True, default=time.strftime('%Y-%m-01'))
    date_to = fields.Date(string="To", required=True,
                          default=str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])
    actual_date_from = fields.Date()
    actual_date_to = fields.Date()
    att_sheet_ids = fields.One2many(comodel_name='attendance.sheet', string='Attendance Sheets',
                                    inverse_name='batch_id')
    attendance_sheets_count = fields.Integer(compute='_compute_attendance_sheets_count')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('att_gen', 'Attendance Sheets Generated')], default='draft', track_visibility='onchange',
        string='Status', readonly=True, )
    payslip_batch_id = fields.Many2one(comodel_name='hr.payslip.run', string='Payslip Batch')

    def _compute_attendance_sheets_count(self):
        for rec in self:
            rec.attendance_sheets_count = len(rec.att_sheet_ids)

    def gen_att_sheet(self, contracts):
        for rec in self:
            rec._create_employees_attendance_sheets(contracts)
            rec.state = 'att_gen'
            rec.att_sheet_ids.write({'state': 'done'})
        #     batch.action_att_gen()

    def back_to_draft(self):
        self.state = 'draft'
        self.att_sheet_ids.unlink()

    # def action_cancel(self):
    #     pass
    # for sheet in self.att_sheet_ids:
    #     sheet.unlink()
    # return self.write({'state': 'draft'})

    def action_open_attendance_sheets(self):
        self.ensure_one()
        try:
            tree_view_id = self.env.ref("jbm_hr_attendance.hr_attendance_sheet_tree_view").id
            form_view_id = self.env.ref("jbm_hr_attendance.hr_attendance_sheet_form_view").id
            # graph_view_id = self.env.ref("jbm_hr_attendance.attendance_sheet_line_graph").id
            # pivot_view_id = self.env.ref("jbm_hr_attendance.attendance_sheet_report_view_pivot").id
        except Exception as e:
            form_view_id = False
            tree_view_id = False
            graph_view_id = False
            pivot_view_id = False

        return {
            "type": "ir.actions.act_window",
            "res_model": "attendance.sheet",
            "view_mode": "tree,graph,pivot,form",
            "views": [[tree_view_id, 'tree'], [form_view_id, 'form']],
            "domain": [['id', 'in', self.att_sheet_ids.ids]],
            "context": {'pivot_measures': ['__count__', 'total_late_early']},
            "name": "Lines",
        }

    def _create_employees_attendance_sheets(self, contracts):
        for att_sheet in self:
            att_sheet.att_sheet_ids.unlink()
        sheet_name = f'Attendance Sheet - {format_date(self.env, self.date_to, date_format="MMMM y")}'

        employees = self.employee_ids
        from_date = self.date_from
        to_date = self.date_to
        if not employees:
            employees = self.env['hr.employee'].search([])
        for employee in employees:
            # contract = self.env['hr.contract'].search([('employee_id', '=', employee.id), ('id', 'in', contracts.ids)])
            # if contract:
            if employee.joining_date and employee.joining_date >= self.date_to:
                continue
                # raise ValidationError(
                #     _("The Hiring Date of employee %s is greater than the selected period") % (employee.name))
            emp_contracts = contracts.get(employee.id)
            if emp_contracts:
                res = {
                    'employee_id': employee.id,
                    'contract_ids': [(6, 0, emp_contracts)],
                    'name': sheet_name,
                    'batch_id': self.id,
                    'date_from': from_date,
                    'date_to': to_date,
                    'actual_date_from': self.actual_date_from,
                    'actual_date_to': self.actual_date_to,
                }
                att_sheet = self.env['attendance.sheet'].create(res)
                # att_sheet._get_employee_contract()
                att_sheet.get_attendances()

    @api.constrains('date_from', 'date_to')
    def _check_start_end_date(self):
        for record in self:
            if record.date_from and record.date_to and record.date_from > record.date_to:
                raise ValidationError("Start date Can't be greater than the end date")
