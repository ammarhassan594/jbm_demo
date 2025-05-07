# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Probation(models.Model):
    _inherit = 'hr.contract'


    # structure_type_id = fields.Many2one('hr.payroll.structure.type', string="Salary Structure Type")
    company_country_id = fields.Many2one('res.country', string="Company country", related='company_id.country_id',
                                         readonly=True)
    wage_type = fields.Selection([('monthly', 'Monthly Fixed Wage'), ('hourly', 'Hourly Wage')])
    hourly_wage = fields.Monetary('Hourly Wage', digits=(16, 2), default=0, required=True, tracking=True,
                                  help="Employee's hourly gross wage.")

    training_info = fields.Text(string='Probationary Info')
    waiting_for_approval = fields.Boolean()
    is_approve = fields.Boolean()
    state = fields.Selection(
        selection=[
            ('draft', 'New'),
            ('probation', 'Probation'),
            ('open', 'Running'),
            ('close', 'Expired'),
            ('cancel', 'Cancelled'),
        ],
    )
    probation_id = fields.Many2one('hr.training')
    half_leave_ids = fields.Many2many('hr.leave', string="Half Leave")
    training_amount = fields.Float(string='Training Amount', help="amount for the employee during training")



    @api.onchange('employee_id')
    def change_employee_id(self):
        """
        function for changing employee id of hr.training if changed
        """
        if self.probation_id and self.employee_id:
            self.probation_id.employee_id = self.employee_id.id

    def action_approve(self):
        """
        function used for changing the state probation into
        running when approves a contract
        """

        self.write({'is_approve': True})
        if self.state == 'draft':
            self.write({'state': 'open',
                        'is_approve': False})

