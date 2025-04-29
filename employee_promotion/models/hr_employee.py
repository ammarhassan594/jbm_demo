from odoo import fields, models, api, _


class ModelName(models.Model):
    _inherit = 'hr.employee'

    promotion_ids = fields.One2many('employee.promotion', 'employee_id', string="Promotions")
    count_promotions = fields.Float(string="Promotions Count", compute="_get_promotion_count")
    degree_id = fields.Many2one('hr.recruitment.degree', string="Degree", required=True)

    @api.depends('promotion_ids')
    def _get_promotion_count(self):
        for rec in self:
            if rec.promotion_ids:
                rec.count_promotions = len(rec.promotion_ids)
            else:
                rec.count_promotions = 0

    def custom_open_promotions(self):
        return {
            'name': _("Promotions"),
            'domain': [('id', 'in', self.promotion_ids.ids)],
            'view_type': 'form',
            'res_model': 'employee.promotion',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }

