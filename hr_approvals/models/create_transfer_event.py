# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import datetime


class CreateTransferEvent(models.TransientModel):
    _name = 'create.transfer.event'
    _description = 'Create Transfer Events wizard'

    related_approval = fields.Many2one('approval.request', 'Related Approval', required=True)
    event_type_id = fields.Many2one(comodel_name='sap.event.type', string='Event Type', required=True)
    event_reason_id = fields.Many2one(comodel_name='sap.event.type.reason', string='Event Reason', required=False)

    @api.onchange('event_type_id')
    def onchange_event_type(self):
        self.event_reason_id = False
        return {'domain': {'event_reason_id': [('event_type_id', '=', self.event_type_id.id)]}}

    def create_transfer_events(self):
        source_dep = self.related_approval.subsection_source if self.related_approval.subsection_source.id else (
            self.related_approval.section_source if self.related_approval.section_source.id else (
                self.related_approval.department_source if self.related_approval.department_source.id else (
                    self.related_approval.department_source if self.related_approval.department_source.id else False)))
        destination_dep = self.related_approval.subsection_destination if self.related_approval.subsection_destination.id else (
            self.related_approval.section_destination if self.related_approval.section_destination.id else (
                self.related_approval.department_destination if self.related_approval.department_destination.id else (
                    self.related_approval.department_destination if self.related_approval.department_destination.id else False)))

        if self.related_approval.transfer_type == 'permanent':
            event = self.env['hr.employee.event'].create({
                'name': self.event_type_id.id,
                'event_reason': self.event_reason_id.id,
                'start_date': self.related_approval.transfer_from_date,
                'end_date': False,
                'employee_id': self.related_approval.employee_transferred.id,
                'is_processed': False,
                'is_triggered': False,
                'related_requisition': self.related_approval.id,
                'is_esd': False
            })
            event.onchange_employee()
            event.org_unit_fkey = destination_dep.id
            event.line_manager_id_fkey = self.related_approval.line_manager_destination.id
            event.shift_type_fkey = self.related_approval.working_shift_destination.id
            event.cost_center_fkey = self.related_approval.cost_center_destination.id
        elif self.related_approval.transfer_type == 'temporary':
            event1 = self.env['hr.employee.event'].create({
                'name': self.event_type_id.id,
                'event_reason': self.event_reason_id.id,
                'start_date': self.related_approval.transfer_from_date,
                'end_date': self.related_approval.transfer_to_date,
                'employee_id': self.related_approval.employee_transferred.id,
                'is_processed': False,
                'is_triggered': False,
                'related_requisition': self.related_approval.id,
                'is_esd': False
            })
            event1.onchange_employee()
            event1.org_unit_fkey = destination_dep.id
            event1.line_manager_id_fkey = self.related_approval.line_manager_destination.id
            event1.shift_type_fkey = self.related_approval.working_shift_destination.id
            event1.cost_center_fkey = self.related_approval.cost_center_destination.id

            event2 = self.env['hr.employee.event'].create({
                'name': self.event_type_id.id,
                'event_reason': self.event_reason_id.id,
                'start_date': self.related_approval.transfer_to_date + datetime.timedelta(days=1),
                'end_date': False,
                'employee_id': self.related_approval.employee_transferred.id,
                'is_processed': False,
                'is_triggered': False,
                'related_requisition': self.related_approval.id,
                'is_esd': False
            })
            event2.onchange_employee()
            event2.org_unit_fkey = source_dep.id
            event2.line_manager_id_fkey = self.related_approval.line_manager_source.id
            event2.shift_type_fkey = self.related_approval.working_shift_source.id
            event2.cost_center_fkey = self.related_approval.cost_center_source.id
