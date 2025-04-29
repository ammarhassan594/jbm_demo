from odoo import fields, models, api, _
from odoo.exceptions import AccessError, ValidationError, UserError


class HrNoticeOffences(models.Model):
    _name = 'hr.notice.offences'
    _description = 'Hr Notice Offences'

    name = fields.Char('Offences')


class HrNotices(models.Model):
    _name = 'hr.notice'
    _description = 'Hr Notice'

    name = fields.Char('Warning Sequence', default="Draft")
    state = fields.Selection([('draft', "Draft"), ('signed', "Signed")], "State", default='draft')

    related_employee = fields.Many2one('hr.employee', "Related Employee")

    related_fusion_id = fields.Char(related='related_employee.fusion_id')
    related_system_id = fields.Char(related='related_employee.system_id')

    related_manager = fields.Many2one('hr.employee', "Manager")
    related_department = fields.Many2one('hr.department', 'Department')
    related_job_title = fields.Char('Job Title')
    date_offence = fields.Date('Date of Offence')
    date_issuing = fields.Date('Date of Issuing Warning Letter')
    date_report_offence = fields.Date('Date of Reporting the Offence')
    type_offence = fields.Many2one("hr.notice.offences", "Warning Type")
    reason = fields.Text('Reason')
    total_days = fields.Char('Total Days')
    user_id = fields.Many2one('res.users', "Responsible User", default=lambda self: self.env.user)
    description = fields.Text('Description', readonly=True)
    attachment_ids = fields.Many2many(comodel_name="ir.attachment",
                                      relation="notice_ir_attachment_document",
                                      column1="notice_id",
                                      column2="attachment_id",
                                      string="File",
                                      required=True
                                      )

    @api.onchange('related_employee')
    def _on_employee_change(self):
        if self.related_employee:
            self.related_manager = self.related_employee.parent_id
            self.related_department = self.related_employee.department_id
            self.related_job_title = self.related_employee.job_title

    def action_signed(self):
        for rec in self:
            rec.write({'name': self.env['ir.sequence'].next_by_code('hr.notice'),
                       'state': 'signed'})

    @api.model
    def create(self, vals):
        if vals.get('attachment_ids', '') == '':
            raise ValidationError(_('Draft Warning File must be filled!'))
        result = super(HrNotices, self).create(vals)
        result.action_signed()
        return result
