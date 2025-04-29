from odoo import fields, models, api, _
from odoo.exceptions import UserError


class OutsourcedEmployeeReportConfig(models.Model):
    _name = 'outsourced.employee.report.config'
    _description = 'Outsourced Employee Report Config'

    name = fields.Char(string='Template Name', compute='compute_template_name', store=True)
    template = fields.Selection([
        ('outsourced_qid_report', 'Outsourced RP Expiry Date Report'),
        ('outsourced_national_address_report', 'Outsourced National Address Report'),
    ], string='Report Template')
    user_ids = fields.Many2many(comodel_name='res.users', string='Users', domain="[('share', '=', False)]")

    @api.depends('template')
    def compute_template_name(self):
        for rec in self:
            rec.name = dict(self._fields['template'].selection).get(self.template)

    @api.constrains('template')
    def check_uniq_template_rec(self):
        rec_ids = self.search([('template', '=', self.template)]) - self
        if rec_ids:
            raise UserError(_('Record For %s Template Already Exist.' % dict(self._fields['template'].selection).get(
                self.template)))
