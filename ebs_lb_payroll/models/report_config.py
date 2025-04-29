from odoo import models, fields, api,_

class EbsHrSalaryReport(models.Model):
    _name = 'ebs.hr.salary.report'
    _description = 'EBS HR Salary Report'

    name = fields.Char('Name')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    salary_report_lines = fields.One2many('ebs.hr.salary.report.lines','salary_report_id')


class EbsHrSalaryReportLines(models.Model):
    _name = 'ebs.hr.salary.report.lines'
    _description = 'EBS HR Salary Report Line'

    name = fields.Char('Name', required=1)
    rule_ids = fields.Many2many('hr.salary.rule', string='Rules', required=1)
    sequence = fields.Integer('Sequence')
    salary_report_id = fields.Many2one('ebs.hr.salary.report')


class EbsHrWPSReport(models.Model):
    _name = 'ebs.hr.wps.config'
    _description = 'EBS HR WPS Config'

    name = fields.Char('Name')
    wps_report_lines = fields.One2many('ebs.hr.wps.lines','wps_config_id')
    template = fields.Selection([('qnb', 'QNB'), ('cbq', 'CBQ')], string="Template", default='qnb')
    bank_account_id = fields.Many2one('res.partner.bank', string="Bank Account", domain="[('partner_id.company_partner','=',True)]")


class EbsHrWPSLines(models.Model):
    _name = 'ebs.hr.wps.lines'
    _description = 'EBS HR WPS Lines'

    name = fields.Char('Name')
    template = fields.Selection([('no_working_days', 'Number of working days'),
                                 ('extra_hours', 'Extra Hours'),
                                 ('payment_type', 'Payment Type'),
                                 ('notes', 'Notes/Comments'),
                                 ('salary_rules', 'Salary Rules')], string='Template')
    rule_ids = fields.Many2many('hr.salary.rule', string='Rules')
    sequence = fields.Integer('Sequence')
    wps_config_id = fields.Many2one('ebs.hr.wps.config')
