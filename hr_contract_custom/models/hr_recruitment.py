# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Applicant(models.Model):
    _inherit = "hr.applicant"

    def _get_contract_values(self):
        values = {
            'group': self.job_id.group.id,
            'department': self.job_id.department_id.id,
            'employee_id': self.emp_id.id,
            'section': self.job_id.section.id,
            'subsection': self.job_id.subsection.id,
            'department_id': self.job_id.subsection.id if self.job_id.subsection.id else (
                self.job_id.section.id if self.job_id.section.id else (
                    self.job_id.department_id.id if self.job_id.department_id.id else (
                        self.job_id.group.id if self.job_id.group.id else False))),
            'job_id': self.job_id.id,
            'applicant_id': self.id,
            # 'wage': self.salary_expected + int(self.salary_expected_extra),
            'date_start': self.availability,
            'cost_center': self.job_id.cost_center.id

        }
        return values

    def generate_contract(self):
        values = self._get_contract_values()
        contract = self.env['hr.contract'].create(values)
        contract.on_change_date_start()
        for line in self.job_id.related_compensations:
            contract.related_compensation |= line.copy()

        return {
            'name': ('Oppen Contract'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.contract',
            'res_id': contract.id,
            'target': 'new',
        }
