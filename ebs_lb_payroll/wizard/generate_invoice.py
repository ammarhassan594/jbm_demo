from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
from itertools import groupby


class GenerateInvoice(models.TransientModel):
    _name = 'generate.invoice'
    _description = 'Generate Invoice'

    type = fields.Selection([('fold','Fold'),('unfold','UnFold')],string="Type",default='fold',required=True)
    payslip_ids = fields.Many2many('hr.payslip', string='Payslip')
    rules_ids = fields.Many2many('hr.salary.rule',string="Rules", domain=[('product_id','!=',False)])

    @api.model
    def default_get(self, fields):
        res = super(GenerateInvoice, self).default_get(fields)
        res.update({'payslip_ids': self._context.get('active_ids')})
        return res

    def generate_invoice(self):
        print("Generate Invoice")
        emps = self.payslip_ids.mapped('employee_id')
        emp_company_mapping = {}
        companies = emps.mapped('partner_parent_id')
        for com in companies:
            employees = self.env['hr.employee'].search([('partner_parent_id', '=', com.id), ('id', 'in', emps.ids)])
            emp_company_mapping.update({com: employees})
        for company in emp_company_mapping:
            invoice_vals = {}
            invoice_line_id_vals = []
            invoice = self.env['account.move'].create({'partner_id':company.id ,'move_type': 'out_invoice', 'invoice_date': date.today()})
            payslips = self.payslip_ids.filtered(lambda x: x.employee_id in emp_company_mapping[company])
            products = payslips.line_ids.mapped('salary_rule_id.product_id')
            product_mapping = {}
            employee_map = {}
            empl_lst = []
            for prod in products:
                payslip = payslips.line_ids.filtered(lambda x: x.salary_rule_id.product_id in prod and x.salary_rule_id in self.rules_ids and x.amount > 0)
                if payslip:
                    product_mapping.update({payslip:prod})
            for emp in payslips.employee_id:
                pay = payslips.line_ids.filtered(lambda x:x.slip_id.employee_id == emp and x.salary_rule_id in self.rules_ids and x.amount > 0)
                employee_map.update({emp:pay})
            for lines in product_mapping:
                invoice_line_vals = {}
                for line in lines:
                    # employee = line.slip_id.employee_id
                    # empl_lst.append([product_mapping[lines],line])
                    # employee_map.update({employee: line})
                    invoice.update({'ref': 'Salary Invoice- %s TO %s' % (line.date_from, line.date_to)})
                    if line.invoice_line_id:
                        line.update({'is_created':True})
                    rule = line.salary_rule_id
                    if rule.product_id and line.amount > 0:
                        if not rule.product_id.property_account_income_id:
                            raise UserError('Please set the income account for %s product of salary rule %s' % (
                            rule.product_id.name, rule.name))
                if self.type == 'fold':
                    lines = lines.filtered(lambda x:x.is_created == False)
                    if lines:
                        amt_total = sum(lines.mapped('amount'))
                        name = product_mapping[lines].name
                        invoice_line_vals.update({
                            'product_id': product_mapping[lines].id,
                            'account_id': product_mapping[lines].property_account_income_id.id,
                            'quantity': 1,
                            'price_unit': amt_total,
                            'name': name,
                            'payslip_line_ids': [(6,0,lines.ids)],
                        })
                        balance = -(amt_total)
                        invoice_line_vals.update({
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                        })
                        if amt_total != 0:
                            invoice_line_id_vals.append((0, 0, invoice_line_vals))
                if self.type == 'unfold':
                    if len(payslips) > 1:
                        for emp in employee_map:
                            amt_total = 0
                            for line_pay in employee_map[emp].filtered(lambda x: x.is_created == False):
                                # is_created = lines.filtered(lambda x: x.is_created == False)
                                # if lines and is_created:
                                if line_pay in lines:
                                    amt_total += line_pay.amount
                            empl_invoice_lines = {}
                            product_name = str(product_mapping[lines].name),
                            empl_invoice_lines.update({
                                    'product_id': product_mapping[lines].id,
                                    'account_id': product_mapping[lines].property_account_income_id.id,
                                    'quantity': 1,
                                    'price_unit': amt_total,
                                    'name': str(product_name[0]) + " - " + str(emp.name),
                                    'payslip_line_ids': [(6, 0, lines.ids)]
                                })
                            balance = -(amt_total)
                            empl_invoice_lines.update({
                                    'debit': balance > 0.0 and balance or 0.0,
                                    'credit': balance < 0.0 and -balance or 0.0,
                            })
                            if amt_total != 0:
                                invoice_line_id_vals.append((0, 0, empl_invoice_lines))
                    else:
                        amt_total = sum(lines.mapped('amount'))
                        name = str(product_mapping[lines].name)[0]
                        invoice_line_vals.update({
                            'product_id': product_mapping[lines].id,
                            # 'analytic_account_id': rule.analytic_account_id and rule.analytic_account_id.id,
                            # 'name': rec.name and rec.name,
                            'account_id': product_mapping[lines].property_account_income_id.id,
                            'quantity': 1,
                            'price_unit': amt_total,
                            'name': name  + " - " + str(payslips.employee_id.name),
                            'payslip_line_ids': [(6, 0, lines.ids)]
                        })
                        balance = -(amt_total)
                        invoice_line_vals.update({
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                        })
                        if amt_total != 0:
                            invoice_line_id_vals.append((0, 0, invoice_line_vals))
            if invoice_line_id_vals:
                for payslip in payslips:
                    payslip.update({'payslipinvoice_ids':[(4,invoice.id)]})
                    # invoice.update({'payslip_id':payslip.id})
                invoice.update({'invoice_line_ids':invoice_line_id_vals})
            if not invoice.invoice_line_ids:
                invoice.unlink()
        return True
           # invoice_vals.update({'': invoice_line_id_vals})
            # invoice.update({'payslip_id': [(6, 0, self.payslip_ids.filtered(
            #                          lambda x: x.employee_id in emp_company_mapping[company]).ids)]})

