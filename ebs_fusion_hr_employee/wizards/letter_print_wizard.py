from odoo import fields, models, api, _


class LetterPrintWizard(models.TransientModel):
    _name = 'letter.print.wizard'
    _description = 'Letter Print Wizard'

    report_action = fields.Selection([
        ('noc_to_waive_notice_period_report_action', 'NOC to Waive Notice Period'),
        ('noc_generic_report_action', 'NOC - Generic'),
        ('salary_certificate_cbq_report_action', 'Salary Certificate – CBQ: QID Holder'),
        ('salary_certificate_qnb_report_action', 'Salary Certificate – QNB: QID Holder'),
        ('salary_certificate_visa_report_action', 'Salary Certificate - QNB - Work Visa Holder Only'),
        ('salary_certificate_visa_cbq_report_action', 'Salary Certificate -  CBQ - Work Visa Holder Only'),
        ('outsourced_employee_liquor_permit', 'QDC Liquor Permit Application'),
        ('salary_certificate_generic_qid_holder', 'Salary Certificate – Generic: QID Holder')
    ], string='Report Template')

    def button_confirm(self):
        model = self._context.get('active_model')
        employee_ids = self.env[model].browse(self.env.context.get('active_ids'))
        for emp in employee_ids:
            company = emp.company_id.search([('partner_id', '=', emp.sponsored_company_id.id)], limit=1)
            emp.write(
                {'comp_hearder': company.company_report_header, 'comp_footer': company.company_report_footer})
        report_action_name = 'ebs_fusion_hr_employee.{}'.format(self.report_action)
        return self.env.ref(report_action_name).report_action(employee_ids)
