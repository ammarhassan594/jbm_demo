from odoo import fields, models, api


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _description = 'HR Resignation'

    state = fields.Selection(
        [('draft', 'Draft'), ('active', 'Active'), ('done', 'Done'), ('extended', 'Resignation Extended'),
         ('cancel', 'Cancelled')],
        string='Status',
        readonly=True, required=True, tracking=True, copy=False, default='draft')
    name = fields.Char('Name', compute='get_employee_name')
    related_employee = fields.Many2one('hr.employee', string="Employee")
    related_contract = fields.Many2one('hr.contract', 'Contract', ondelete='cascade')
    extended_from = fields.Many2one('hr.resignation', 'Extended From', readonly=True)

    # can_do_survey = fields.Boolean('can do interview', compute="_can_do_survey")
    # can_approve_survey = fields.Boolean('can approve interview', compute="_can_approve_survey")
    # calculate_due_date = fields.Boolean('Cal', compute="_calculate_get_due_date")
    # due_date = fields.Integer('Due Date', compute="_get_due_date", store=True)

    @api.depends('related_employee')
    def get_employee_name(self):
        for rec in self:
            rec.name = (rec.related_employee.name if rec.related_employee.name else '') + ' Resignation'

    def set_done(self):
        self.write({'state': 'done'})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def set_cancel(self):
        self.write({'state': 'cancel'})
        self.related_contract.write(
            {'effective_end_date': self.related_contract.date_end})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def set_active(self):
        self.write({'state': 'active'})
        self.related_contract.write(
            {'effective_end_date': self.end_date})

    def set_extend(self):
        self.write({'state': 'extended'})

    def _get_warnings(self):
        self = self.sudo()
        full_date_format = '%d/%m/%Y'
        line = []
        for warning in self.related_approval.related_warnings:
            line.append(
                {'name': warning.name, 'type_offence': warning.type_offence.name,
                 'create_date': warning.create_date.strftime(full_date_format) if warning.create_date else '',
                 'date_issuing': warning.date_issuing.strftime(full_date_format) if warning.date_issuing else '',
                 'date_offence': warning.date_offence.strftime(full_date_format) if warning.date_offence else '',
                 'date_report_offence': warning.date_report_offence.strftime(
                     full_date_format) if warning.date_report_offence else '', 'total_days': warning.total_days,
                 'reason': warning.reason})
        return line

    def _get_approvers(self):
        self = self.sudo()
        full_date_format = '%d/%m/%Y'
        line = []
        for approver in self.related_approval.approver_ids:
            line.append(
                {'sequence': approver.sequence, 'user_id': approver.user_id.name,
                 'approver_category': approver.approver_category,
                 'approval_date': approver.approval_date.strftime(full_date_format) if approver.approval_date else '',
                 'status': dict(approver._fields['status'].selection).get(approver.status),
                 'reject_reason': approver.reject_reason,
                 'replacement_position': dict(approver._fields['replacement_position'].selection).get(
                     approver.replacement_position),
                 'eligible_rehire': dict(approver._fields['eligible_rehire_selection'].selection).get(
                     approver.eligible_rehire_selection),
                 'eligible_rehire_comment': approver.eligible_rehire_comment})
        return line

    @api.model
    def create(self, vals):
        self = self.sudo()
        res = super(HrResignation, self).create(vals)
        res.state = 'active'
        res.related_contract.effective_end_date = res.end_date
        return res
