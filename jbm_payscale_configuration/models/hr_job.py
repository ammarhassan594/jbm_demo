from odoo import models, fields, api


class HRJobCustom(models.Model):
    _inherit = 'hr.job'

    level = fields.Selection(string="Level", default="",
                             selection=[('director', 'Department Director'),
                                        ('manager', 'Department Manager'),
                                        ('assistant_manager', 'Department Manager Assistant'),
                                        ('others', 'Others')])
    payscale_id = fields.Many2one(comodel_name="employee.payscale", string="Payscale", required=False, )
