# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime, date

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
    'years': lambda interval: relativedelta(minutes=interval)
}


class ScheduledEntriesConfiguration(models.Model):
    _name = 'scheduled.entries.configuration'
    _description = 'Scheduled Entries Configuration'
    _rec_name = 'code'

    code = fields.Char(string="Code")
    description = fields.Text(string="Description")
    number_of_periods = fields.Integer(string="Number of Periods")
    scheduled_period = fields.Selection([('minutes', 'Minutes'),
                                         ('hours', 'Hours'),
                                         ('days', 'Days'),
                                         ('months', 'Months'),
                                         ('years', 'Years')], string="Schedule")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], string="Status", default='draft')
    scheduled_entries_lines = fields.One2many('scheduled.entries.lines', 'entries_configuration_id',
                                              string="Scheduled Entries lines")
    date = fields.Datetime(string="Date", default=fields.Datetime.now())
    last_call = fields.Datetime(string="Last call")
    # next_call = fields.Datetime(string="Next call", compute="compute_next_call")
    next_call = fields.Datetime(string="Next call", compute="compute_next_call", store=True)
    move_ids = fields.Many2many('account.move', string="Journal Entries")

    is_set_last_call_date = fields.Boolean(string="Is set last call date", compute="compute_is_set_last_call_date")

    @api.depends()
    def compute_is_set_last_call_date(self):
        for record in self:
            current_last_call = False
            if record.next_call < datetime.now():
                current_last_call = datetime.now() - relativedelta(minutes=record.number_of_periods)
            # if record.scheduled_period == 'minutes' and record.number_of_periods == 1:
            #     current_last_call = datetime.now() - relativedelta(minutes=record.number_of_periods)
            # elif record.scheduled_period == 'hours':
            #     current_last_call = datetime.now() -  relativedelta(hours=record.number_of_periods)
            # elif record.scheduled_period == 'days':
            #     current_last_call = datetime.now() -  relativedelta(days=record.number_of_periods)
            # elif record.scheduled_period == 'months':
            #     current_last_call = datetime.now() -  relativedelta(months=record.number_of_periods)
            # elif record.scheduled_period == 'years':
            #     current_last_call = datetime.now() -  relativedelta(years=record.number_of_periods)
            if current_last_call and record.last_call != current_last_call:
                record.last_call = current_last_call
            record.is_set_last_call_date = True

    @api.depends('date', 'number_of_periods', 'scheduled_period', 'last_call')
    # @api.depends()
    def compute_next_call(self):
        for record in self:
            if record.date and record.number_of_periods and record.scheduled_period:
                test_date = record.date
                future_nextcall = False
                if record.last_call:
                    past_nextcall = fields.Datetime.to_datetime(record.last_call)
                    interval = _intervalTypes[record.scheduled_period](record.number_of_periods)
                    now = datetime.utcnow()
                    missed_call = past_nextcall
                    missed_call_count = 0
                    while missed_call <= now:
                        missed_call += interval
                        missed_call_count += 1
                    future_nextcall = missed_call
                    if future_nextcall:
                        # record.next_call = future_nextcall
                        test_date = False
                    else:
                        test_date = record.last_call
                if record.scheduled_period == 'minutes' and test_date:
                    record.next_call = test_date + relativedelta(minutes=record.number_of_periods)
                elif record.scheduled_period == 'hours' and test_date:
                    record.next_call = test_date + relativedelta(hours=record.number_of_periods)
                elif record.scheduled_period == 'days' and test_date:
                    record.next_call = test_date + relativedelta(days=record.number_of_periods)
                elif record.scheduled_period == 'months' and test_date:
                    record.next_call = test_date + relativedelta(months=record.number_of_periods)
                elif record.scheduled_period == 'years' and test_date:
                    record.next_call = test_date + relativedelta(years=record.number_of_periods)
                elif future_nextcall:
                    record.next_call = future_nextcall
                else:
                    record.next_call = record.date
            else:
                record.next_call = False

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def generate_scheduled_entries(self):
        records = self.search([('state', '=', 'confirm')])
        for record in records:
            if record.next_call.date() == date.today() and record.next_call.minute == datetime.now().minute:
                record.sudo().write({'last_call': datetime.now()})
                if record.scheduled_entries_lines:
                    print("-----------------------")
                    move_vals = {
                        'move_type': 'entry',
                        'date': date.today(),
                        'company_id': self.env.company.id,
                        'ref': record.code,
                    }
                    move_line_vals = []
                    for line in record.scheduled_entries_lines:
                        if line.credit > 0:
                            move_line_vals.append((0, 0, {
                                'name': line.account_id.name,
                                'account_id': line.account_id.id,
                                'debit': 0.0,
                                'credit': line.credit,
                                'partner_id': line.partner_id.id,
                                'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else False
                            }))
                        if line.debit > 0:
                            move_line_vals.append((0, 0, {
                                'name': line.account_id.name,
                                'account_id': line.account_id.id,
                                'debit': line.debit,
                                'credit': 0.0,
                                'partner_id': line.partner_id.id,
                                'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else False
                            }))
                    if move_line_vals:
                        move_vals.update(
                            {'line_ids': move_line_vals})
                        move = self.env['account.move'].sudo().create(move_vals)
                        if move:
                            record.sudo().write({'move_ids': [(4, move.id)]})


class ScheduledEntriesLines(models.Model):
    _name = 'scheduled.entries.lines'
    _description = 'Scheduled Entries Lines'

    entries_configuration_id = fields.Many2one('scheduled.entries.configuration', string="Entries Configuration id")
    account_id = fields.Many2one('account.account', string="Account")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    analytic_tag_id = fields.Many2one('account.analytic.tag', string="Analytic Tag")
    debit = fields.Monetary(string="Debit")
    credit = fields.Monetary(string="Credit")
    partner_id = fields.Many2one('res.partner', string="Partner")
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
