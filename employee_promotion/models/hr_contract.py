from odoo import fields, models, api, _
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


class InheritHrContract(models.Model):
    _inherit = 'hr.contract'

    name = fields.Char()

    def action_draft_contract(self):
        for record in self.browse(self.env.context['active_ids']):
            record.write({
                'state': 'draft'
            })

    def action_probation_contract(self):
        for record in self.browse(self.env.context['active_ids']):
            record.write({
                'state': 'probation'
            })

    def action_open_contract(self):
        for record in self.browse(self.env.context['active_ids']):
            record.write({
                'state': 'open'
            })
            record.onchange_contract_validity()

    def action_close_contract(self):
        for record in self.browse(self.env.context['active_ids']):
            record.write({
                'state': 'close'
            })

    def copy(self, default=None):
        default = dict(default or {})
        default['resource_calendar_id'] = self.resource_calendar_id.id
        return super(InheritHrContract, self).copy(default)

    @api.model
    def update_state(self):
        from_cron = 'from_cron' in self.env.context
        contracts = self.search([
            ('state', '=', 'open'),
            '&',
            ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=7))),
            ('date_end', '>=', fields.Date.to_string(date.today() + relativedelta(days=1))),
        ])
        for contract in contracts:
            contract.activity_schedule(
                'mail.mail_activity_data_todo', contract.date_end,
                _("The contract of %s is about to expire.", contract.employee_id.name),
                user_id=contract.hr_responsible_id.id or self.env.uid)

        if contracts:
            contracts._safe_write_for_cron({'kanban_state': 'blocked'}, from_cron)

        contracts_to_close = self.search([
            ('state', '=', 'open'),
            ('date_end', '<=', fields.Date.to_string(date.today()))
        ])

        if contracts_to_close:
            contracts_to_close._safe_write_for_cron({'state': 'close'}, from_cron)

        contracts_to_open = self.search([('state', '=', 'draft'), ('kanban_state', '=', 'done'),
                                         ('date_start', '<=', fields.Date.to_string(date.today())), ])

        if contracts_to_open:
            contracts_to_open._safe_write_for_cron({'state': 'open'}, from_cron)

        contract_ids = self.search([('date_end', '=', False), ('state', '=', 'close'), ('employee_id', '!=', False)])
        # Ensure all closed contract followed by a new contract have a end date.
        # If closed contract has no closed date, the work entries will be generated for an unlimited period.
        for contract in contract_ids:
            next_contract = self.search([
                ('employee_id', '=', contract.employee_id.id),
                ('state', 'not in', ['cancel', 'new']),
                ('date_start', '>', contract.date_start)
            ], order="date_start asc", limit=1)
            if next_contract:
                contract._safe_write_for_cron({'date_end': next_contract.date_start - relativedelta(days=1)}, from_cron)
                continue
            next_contract = self.search([
                ('employee_id', '=', contract.employee_id.id),
                ('date_start', '>', contract.date_start)
            ], order="date_start asc", limit=1)
            if next_contract:
                contract._safe_write_for_cron({'date_end': next_contract.date_start - relativedelta(days=1)}, from_cron)

        today = date.today()
        employee_promotion = self.env['employee.promotion'].search([
            ('date_start', '=', today), ('state', '=', 'approve'), ('promoted', '=', False)
        ])
        for promotion in employee_promotion:
            promotion.contract_id.state = 'close'
            promotion.promoted = True
            old_contract = promotion.contract_status_old
            new_contract = promotion.contract_status_new
            if old_contract and new_contract and old_contract != new_contract:
                promotion.employee_id.write({'contract_status': new_contract})
        six_month_expiry_contracts = self.search([
            ('state', '=', 'open'),
            ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(months=6)))])
        users_to_notify = self.env.ref('jbm_group_access_right_extended.custom_hr_user').users + \
                          self.env.ref('jbm_group_access_right_extended.custom_hr_manager').users
        for contract in six_month_expiry_contracts:
            for user in users_to_notify:
                contract.with_context(mail_activity_quick_update=True).activity_schedule(
                    'employee_promotion.mail_activity_type_contract_expiry',
                    user_id=user.id,
                    summary='Contract {} will expire in less than 6 months '.format(contract.display_name),
                    date_deadline=date.today()
                )
        return True
