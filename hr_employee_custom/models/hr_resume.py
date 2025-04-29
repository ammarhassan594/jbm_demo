from odoo import fields, models, api


class ResumeLineType(models.Model):
    _inherit = 'hr.resume.line.type'

    type = fields.Selection([('nor', 'Normal'), ('edu', 'Education'), ('exp', 'Experience')], 'Resume Type')


class MajorSubject(models.Model):
    _name = 'hr.major.subject'
    _description = 'HR Major Subject'

    name = fields.Char('Majors')


class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'

    education_level = fields.Many2one('hr.recruitment.degree', 'Education Level')

    educational_status = fields.Selection([('completed', 'Completed'), ('ongoing', 'Ongoing')],
                                          'Educational Status')
    major_subject = fields.Many2one('hr.major.subject', 'Major Subject')

    institute_name = fields.Char('Institute Name')
    awarded_country = fields.Many2one('res.country', 'Awarded Country')
    company_name = fields.Char('Company Name')
    type_business = fields.Char('Type Of Business')
    job_title = fields.Char('Job/Position Title')
    work_city = fields.Char('Work City')
    work_country = fields.Many2one('res.country', 'Work Country')

    attachment_ids = fields.Many2many(comodel_name="ir.attachment",
                                      relation="experience_ir_attachment_document",
                                      column1="experience_id",
                                      column2="attachment_id",
                                      string="File"
                                      )
    related_line_type = fields.Selection(related="line_type_id.type")
