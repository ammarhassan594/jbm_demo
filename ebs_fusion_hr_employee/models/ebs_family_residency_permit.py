from odoo import api, fields, models, _


class EbsFamilyResidencyPermit(models.Model):
    _name = 'ebs.family.residency.permit'
    _rec_name = 'family_detail_id'

    employee_id = fields.Many2one('hr.employee')
    family_detail_id = fields.Many2one("ebs.family.details", string='Name', domain="[('employee_id','=',employee_id)]",
                                       required=1)
    dependents_id = fields.Many2one('documents.document', string="Dependents ID No")
    occupation = fields.Char("Occupation")
    residency_type = fields.Selection([('entry', 'Entry Visas'), ('work', 'Work Residence Permit'), ('id', 'ID Cards'),
                                       ('family', 'Family Residence Visa'), ('exit', 'Exit Permit'),
                                       ('consular', 'Consular Services')],
                                      string="Residency type")
    text = fields.Text("Others/Comments")

    @api.model
    def default_get(self, fields):
        result = super(EbsFamilyResidencyPermit, self).default_get(fields)
        result['employee_id'] = self._context.get('params').get('id')
        return result
