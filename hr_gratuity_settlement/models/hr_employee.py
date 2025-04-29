from odoo import fields, models, _, api
from odoo.osv import expression
from datetime import date


class HrEmployeeProbation(models.Model):
    _inherit = 'hr.employee'

    total_working_years = fields.Float(string='Total Years Worked', readonly=True, store=True,
                                       help="Total working years")
    total_working_days = fields.Float(string='Total Days Worked', readonly=True, store=True)
    salary_rate = fields.Float(string='Salary Rate', readonly=True, store=True)
    total_amount_working_days_no_store = fields.Float(string='End of Service Benefit', readonly=True,
                                                      compute='_onchange_gratuity_payment')
    eos_a_amount = fields.Float(string='EOS Advance', readonly=True,
                                                      compute='_onchange_gratuity_payment')
    employee_unpaid_leaves_days = fields.Float(string='Unpaid Leaves(Days)', readonly=True, store=True,
                                               help="Employee Unpaid Leaves days")
    employee_gratuity_duration = fields.Many2one('gratuity.configuration',
                                                 readonly=True,
                                                 string='Configuration Line')

    can_see_end_of_service = fields.Boolean("Can See End Of Service", compute="_check_end_of_service")

    def _default_user(self):
        return self.env.user

    current_user = fields.Many2one('res.users', default=_default_user, compute="_compute_current_user")

    @api.depends('current_user')
    def _check_end_of_service(self):
        for emp in self:
            if not (emp.current_user.has_group('hr_payroll.group_hr_payroll_user') or
                    emp.current_user.has_group('hr_payroll.group_hr_payroll_manager')):
                emp.can_see_end_of_service = False
            else:
                emp.can_see_end_of_service = True

    def _compute_current_user(self):
        for rec in self:
            rec.current_user = self.env.user

    @api.depends('total_working_years', 'salary_rate', 'total_working_days', 'employee_unpaid_leaves_days')
    def _onchange_gratuity_payment(self):
        """ calculating the gratuity pay based on the contract and gratuity
        configurations"""
        for each in self:
            each.total_amount_working_days_no_store = 0
            # if not each.total_working_years and not each.total_working_days and not each.salary_rate and not each.employee_unpaid_leaves_days:
            # if not each.employee_unpaid_leaves_days:  # comment this line to calculate Benefit of end services
            each.total_amount_working_days_no_store = 0
            each.eos_a_amount = 0
            leave_id = each.env['hr.leave.type'].search([('name', '=', 'UNPAID')], limit=1)
            unpaid_leave_ids = each.env['hr.leave'].search([('employee_id', '=', each.id),
                                                            ('holiday_status_id', '=', leave_id.id),
                                                            ('state', '=', 'validate')])
            if len(each.contract_id) > 1 or not each.contract_id:
                each.total_amount_working_days_no_store = 0
                each.eos_a_amount = 0
                return True
            each.employee_unpaid_leaves_days = employee_unpaid_leaves_days = 0
            # find total unpaid leaves days
            for unpaid_leave in unpaid_leave_ids:
                employee_unpaid_leaves_days += unpaid_leave.number_of_days
            each.employee_unpaid_leaves_days = employee_unpaid_leaves_days
            gratuity_duration_id = False
            if each.country_id.code == 'QA':
                nationality = 'QA'
            else:
                nationality = 'expatriate'
            hr_accounting_configuration_id = each.env[
                'hr.gratuity.accounting.configuration'].search(
                [('active', '=', True), ('config_contract_type', '=', 'unlimited'),
                 ('nationality', '=', nationality),
                 '|', ('gratuity_end_date', '>=', date.today()), ('gratuity_end_date', '=', False),
                 '|', ('gratuity_start_date', '<=', date.today()), ('gratuity_start_date', '=', False)])
            print('hr_accounting_configuration_id', hr_accounting_configuration_id)

            if len(hr_accounting_configuration_id) > 1:
                each.total_amount_working_days_no_store = 0
                each.eos_a_amount = 0
                return True
            elif not hr_accounting_configuration_id:
                each.total_amount_working_days_no_store = 0
                each.eos_a_amount = 0
                return True
            # find configuration ids related to the gratuity accounting configuration
            # each.employee_gratuity_configuration = hr_accounting_configuration_id.id
            conf_ids = hr_accounting_configuration_id.gratuity_configuration_table.mapped('id')
            each.total_working_days = (date.today() - each.joining_date).days
            each.total_working_years = each.total_working_days / 365
            hr_duration_config_ids = each.env['gratuity.configuration'].browse(conf_ids)
            for duration in hr_duration_config_ids:
                if duration.from_year and duration.to_year and \
                        duration.from_year <= each.total_working_years <= duration.to_year:
                    gratuity_duration_id = duration
                    break
                elif duration.from_year and not duration.to_year and duration.from_year <= each.total_working_years:
                    gratuity_duration_id = duration
                    break
                elif duration.to_year and not duration.from_year and each.total_working_years <= duration.to_year:
                    gratuity_duration_id = duration
                    break
            if gratuity_duration_id:
                each.employee_gratuity_duration = gratuity_duration_id.id
                each.total_amount_working_days_no_store = 0
                each.eos_a_amount = 0
            else:
                each.total_amount_working_days_no_store = 0
                each.eos_a_amount = 0
                return True
            if each.employee_gratuity_duration and each.contract_id.wage_type == 'monthly':
                if each.employee_gratuity_duration.employee_daily_wage_days != 0:
                    each.salary_rate = ((each.contract_id.wage /
                                         each.employee_gratuity_duration.employee_daily_wage_days) *
                                        each.employee_gratuity_duration.employee_working_days) * \
                                       each.employee_gratuity_duration.percentage
                else:
                    each.total_amount_working_days_no_store = 0
                    each.eos_a_amount = 0
                    return True
            else:
                each.total_amount_working_days_no_store = 0
                each.eos_a_amount = 0
                return True
            if not each.joining_date:
                each.total_amount_working_days_no_store = 0
                each.eos_a_amount = 0
                return True
            # each.total_working_days = (date.today() - each.joining_date).days
            # each.total_working_years = each.total_working_days / 365
            eos_advance = each.env['allowance.request'].search([('allowance_type.code', '=', 'eosb'),
                                                                ('employee_id', '=', each.id), ('state', '=', 'paid')])
            eos_a_amount = round(sum(eos_advance.mapped('requested_amount')), 2) if eos_advance else 0
            each.total_amount_working_days_no_store = ((each.total_working_days - each.employee_unpaid_leaves_days) / 365) * each.salary_rate
            each.eos_a_amount = eos_a_amount
            if each.total_working_years < 1:
                each.total_amount_working_days_no_store = 0
                each.eos_a_amount = 0

    # def generate_work_entries(self, date_start, date_stop):
    #     """
    #     function is used for Generate work entries When
    #     Contract State in Probation,Running,Expired
    #
    #     """
    #     date_start = fields.Date.to_date(date_start)
    #     date_stop = fields.Date.to_date(date_stop)
    #
    #     if self:
    #         current_contracts = self._get_contracts(date_start, date_stop, states=['probation', 'open', 'close'])
    #     else:
    #         current_contracts = self._get_all_contracts(date_start, date_stop, states=['probation', 'open', 'close'])
    #
    #     return bool(current_contracts._generate_work_entries(date_start, date_stop))

    # override the existing function for considering the probation contracts
    def _get_contracts(self, date_from, date_to, states=['open', 'probation'], kanban_state=False):
        """
        Returns the contracts of the employee between date_from and date_to
        """
        state_domain = [('state', 'in', states)]
        if kanban_state:
            state_domain = expression.AND([state_domain, [('kanban_state', 'in', kanban_state)]])

        return self.env['hr.contract'].search(
            expression.AND([[('employee_id', 'in', self.ids)],
                            state_domain,
                            [('date_start', '<=', date_to),
                             '|',
                             ('date_end', '=', False),
                             ('date_end', '>=', date_from)]]))
