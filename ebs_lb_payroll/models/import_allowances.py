# -*- coding: utf-8 -*-
import tempfile

import binascii

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
import xlrd
import xlwt
import base64
import io


class ImportAllowances(models.Model):
    _name = 'ebspayroll.import.allowances'
    _description = 'Import Allowances'
    _rec_name = 'client_id'
    client_id = fields.Many2one('res.partner', string="Client",
                                domain=[('is_customer', '=', True),
                                        ('is_company', '=', True), ('parent_id', '=', False)])
    configuration_id = fields.Many2one('ebspayroll.import.allowances.conf', string="Template", ondelete='restrict')
    date = fields.Date('Date')
    file = fields.Binary('File')
    status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string="State", default="draft")
    element_count = fields.Integer('Element Count',compute='additional_element_count')

    def additional_element_count(self):
        additional_element = self.env['ebspayroll.additional.elements'].search([])
        elements = additional_element.lines.filtered(lambda x:x.import_allowance_id.id == self.id)
        self.element_count = len(elements)

    def action_see_element(self):
        additional_element = self.env['ebspayroll.additional.elements'].search([])
        elements = additional_element.lines.filtered(lambda x:x.import_allowance_id.id == self.id)
        action = self.env.ref('ebs_lb_payroll.additional_element_lines_window').read([])[0]
        action['domain'] = [('id', '=', elements.ids)]
        return action

    def unlink(self):
        for rec in self:
            if rec.status == 'done':
                raise UserError(_("Can Not Delete Done Records."))
        return super(ImportAllowances, self).unlink()

    def add_element(self):
        additional_element_obj = self.env['ebspayroll.additional.elements']
        additional_element_type_obj = self.env['ebspayroll.additional.element.types']

        try:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except:
            raise Warning(_("Invalid file!"))
        first_row = []  # The row where we stock the name of the column
        for col in range(sheet.ncols):
            first_row.append(sheet.cell_value(1, col))
        data = []
        for row in range(2, sheet.nrows):
            elm = {}
            for col in range(sheet.ncols):
                elm[first_row[col]] = sheet.cell_value(row, col)
            data.append(elm)
        conf_lines = self.configuration_id.lines
        type_dict = {}
        type_ids = []
        for ln in data[0].keys():
            type_id_list = []
            type_check = conf_lines.filtered(lambda x: x.label == ln and x.template == 'additional_element_type')
            if type_check:
                type_id_list = type_dict.get(type_check.additional_type.id) or []
                type_id_list.append(type_check.label)
                type_dict.update({type_check.additional_type.id:type_id_list})
                type_ids.append(type_check.additional_type.id)
        for result in data:
            pdate = self.date
            emps = self.env['hr.employee'].search([('qid_no','=',str(int(float(result.get('QID No.')))))])
            payslip_id = self.env['hr.payslip'].search([('date_from', '<=', pdate), ('date_to', '>=', pdate),(
                'state', 'in', ['draft','verify'])], limit=1)
            client = emps.partner_parent_id
            additionals = additional_element_type_obj.search([('id', 'in', type_ids)])
            for additional in additionals:
                name = type_dict[additional.id]
                amt = 0
                for element in name:
                    if result.get(element):
                        amt += result.get(element)
                additional_elements = additional_element_obj.search(
                    [('type', '=', additional.id), ('payment_date', '=', pdate),
                     ('client_id', '=', client.id)])
                if not additional_elements:
                    if emps and amt != 0 and client:
                        element = additional_element_obj.create(
                            {'type': additional.id, 'client_id': client.id, 'payment_date': pdate,
                             'company_id': self.env.company.id,
                             'lines': [(0, 0, {'employee': emps.id, 'amount': amt, 'import_allowance_id': self.id})]})
                        element.confirm_element()
                else:
                    if emps and amt != 0 and client:
                        check_emp = additional_elements.lines.filtered(
                            lambda x: x.employee == emps)
                        if check_emp:
                            additional_elements.write({'lines': [(1, check_emp.id, {'amount': check_emp.amount + amt})]})
                            additional_elements.confirm_element()
                        else:
                            additional_elements.write({'lines': [
                                (0, 0, {'employee': emps.id, 'amount': amt, 'import_allowance_id': self.id})]})
                            additional_elements.confirm_element()

            for line in conf_lines.filtered(lambda o: o.template != 'additional_element_type'):
                if payslip_id:
                    if line.template == 'comment':
                        payslip_id.comments += result.get(line.label)
                        if payslip_id.comments:
                            payslip_id.deduction_reason = '99'
                    if line.template == 'no_working_days':
                        working_day_line = payslip_id.worked_days_line_ids.filtered(lambda o: o.work_entry_type_id.code == 'WORK100')
                        if working_day_line:
                            working_day_line.write({'number_of_days': result.get(line.label)})
                        else:
                            attendence_type_id = self.env['hr.work.entry.type'].search([('code', '=', 'WORK100')])
                            working_vals = {'work_entry_type_id': attendence_type_id, 'number_of_days': result.get(line.label)}
                            payslip_id.write({'worked_days_line_ids': [(0, 0, working_vals)]})

                    # payslip_id.compute_sheet()
        self.write({'status':'done'})
        return True