from odoo import fields, models, api
from odoo.exceptions import AccessError, ValidationError, UserError
import datetime


class ProbationWizardCustom(models.TransientModel):
    _inherit = 'trial.period.l2.wizard'

    employee_id = fields.Many2one(related='related_trial_period.related_employee')
    event_type_id = fields.Many2one('sap.event.type', string='Event Type', required=False, relation='sap.event.type')
    event_reason_id = fields.Many2one('sap.event.type.reason', string='Event Reason', required=False,
                                      relation='sap.event.type.reason')

    @api.onchange('event_type_id')
    def onchange_event_type(self):
        return {'domain': {'event_reason_id': [('event_type_id', '=', self.event_type_id.id)]}}

    @api.onchange('l2_decision')
    def onchange_decision(self):
        for rec in self:
            default_event_type = self.env['sap.event.type'].search([('is_probation', '=', True)], limit=1)
            rec.event_type_id = default_event_type.id

    def submit_l2(self):
        self = self.sudo()
        decision = self.l2_decision
        if decision == 'confirm':
            conf_date = self.related_trial_period.related_contract.trial_date_end + datetime.timedelta(
                days=1)
            self.related_trial_period.write(
                {'state': 'done', 'l2_decision': self.l2_decision, 'l2_justification': self.l2_justification,
                 'confirmation_date': conf_date})
            self.related_trial_period.related_contract.write(
                {'confirmation_date': conf_date})
            # template = self.env.ref('auth_signup.mail_template_data_unregistered_users').with_context({
            #     'email_to': self.related_employee.user_partner_id.email})
            # template.send_mail(self.env.user)
            self.related_trial_period.related_contract.message_notify(
                partner_ids=self.related_trial_period.related_employee.user_partner_id.ids,
                body="Probation assessment done, employee's employment has been confirmed",
                subject="Assessment")

            event = self.env['hr.employee.event'].create({
                'name': self.event_type_id.id,
                'event_reason': self.event_reason_id.id,
                'start_date': datetime.datetime.now(),
                'end_date': False,
                'employee_id': self.employee_id.id,
                'is_processed': False,
                'is_triggered': True,
                'is_esd': False
            })
            event.onchange_employee()
            event.probation_end_date = self.employee_id.contract_id.trial_date_end
            event.confirmation_date = self.employee_id.contract_id.confirmation_date

            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        elif decision == 'terminate':
            self.related_trial_period.related_contract.write(
                {'state': 'cancel'})
            self.related_trial_period.write(
                {'state': 'terminated', 'l2_decision': self.l2_decision, 'l2_justification': self.l2_justification})
        elif decision == 'extend':
            if not self.related_trial_period.extended_from:
                self.env['trial.period'].create({
                    'start_date': self.related_trial_period.end_date + datetime.timedelta(
                        days=1),
                    'end_date': self.related_trial_period.end_date + datetime.timedelta(
                        days=1) + datetime.timedelta(
                        days=self.related_trial_period.related_contract.job_id.job_grade.probation_period),
                    'related_contract': self.related_trial_period.related_contract.id,
                    'extended_from': self.id
                })
                self.related_trial_period.related_contract.write(
                    {'trial_date_end': self.related_trial_period.end_date + datetime.timedelta(
                        days=1) + datetime.timedelta(
                        days=self.related_trial_period.related_contract.job_id.job_grade.probation_period), })
                self.related_trial_period.write(
                    {'state': 'extended', 'l2_decision': self.l2_decision, 'l2_justification': self.l2_justification})
                self.related_trial_period.related_contract.message_notify(
                    partner_ids=self.related_trial_period.related_employee.user_partner_id.ids,
                    body="Probation assessment done, The probation period will been extended till %s" % (
                        self.related_trial_period.related_contract.trial_date_end),
                    subject="Assessment")

                event = self.env['hr.employee.event'].create({
                    'name': self.event_type_id.id,
                    'event_reason': self.event_reason_id.id,
                    'start_date': datetime.datetime.now(),
                    'end_date': False,
                    'employee_id': self.employee_id.id,
                    'is_processed': False,
                    'is_triggered': True,
                    'is_esd': False
                })
                event.onchange_employee()
                event.probation_end_date = self.employee_id.contract_id.trial_date_end
                event.confirmation_date = self.employee_id.contract_id.confirmation_date

                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            else:
                raise ValidationError('Probation Assessment cannot be extended twice!')
