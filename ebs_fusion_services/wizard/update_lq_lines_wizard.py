from odoo import api, fields, models, _


class UpdateLQLinesWizard(models.TransientModel):
    _name = "update.lq.lines.wizard"
    _description = 'Update LQ Lines Wizard'

    def get_sublines(self):
        print("========================", self._context)
        lines = self.env['labor.quota.line'].search(
            [('labor_id', '=', self._context.get('labor_quota_id') if self._context.get('labor_quota_id') else [])])
        if self._context.get('request_type') == 'release':
            return [('line_id', 'in', lines.ids), ('status', '=', 'booked')]
        if self._context.get('request_type') == 'manage':
            return [('line_id', 'in', lines.ids), ('status', '=', 'available')]

    labor_quota_subline_ids = fields.Many2many('labor.quota.subline', string="Labor Quota Lines",
                                               domain=get_sublines)

    def confirm_button(self):
        update_lines = []
        for line in self.labor_quota_subline_ids:
            vals = {
                'labor_quota_line_id': line.line_id.id,
                'labor_quota_subline_id': line.id,
                'ref_no': line.ref_no,
                'nationality_id': line.nationality_id.id,
                'job_id': line.job_id.id,
                'gender': line.gender,
                'status': line.status,
                'employee_id': line.employee_id.id,
            }
            update_lines.append((0, 0, vals))
        service_order_id = self.env['ebs.crm.service.process'].browse(self._context.get('active_id'))
        service_order_id.manage_labor_quota_line_ids = [(5, 0, 0)]
        service_order_id.write({'manage_labor_quota_line_ids': update_lines})
