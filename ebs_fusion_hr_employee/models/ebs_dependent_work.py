from odoo import api, fields, models, _


class EbsDependentWork(models.Model):
    _name = 'ebs.dependent.work'
    _description = 'EBS Dependent Work'

    employee_id = fields.Many2one('hr.employee')

    dependent_id = fields.Many2one('documents.document', string="Dependent ID No")
    work_permit_id = fields.Many2one('documents.document', string="Work Permit No")
    company_phone = fields.Char("Company Phone")
    working_address = fields.Text("Working Address")
    text = fields.Text("Others/Comments")

    @api.model
    def default_get(self, fields):
        result = super(EbsDependentWork, self).default_get(fields)
        result['employee_id'] = self._context.get('params').get('id')
        return result
