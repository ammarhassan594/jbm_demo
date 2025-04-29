# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


class JobOrgChartController(http.Controller):
    _managers_level = 5  # FP request

    def _check_job(self, job_id, **kw):
        if not job_id:  # to check
            return None
        job_id = int(job_id)

        if 'allowed_company_ids' in request.env.context:
            cids = request.env.context['allowed_company_ids']
        else:
            cids = [request.env.company.id]

        Job = request.env['hr.job'].with_context(allowed_company_ids=cids)
        # check and raise
        if not Job.check_access_rights('read', raise_exception=False):
            return None
        try:
            Job.browse(job_id).check_access_rule('read')
        except AccessError:
            return None
        else:
            return Job.browse(job_id)

    def _prepare_job_data(self, job):
        job = job.sudo()
        return dict(
            id=job.id,
            name=job.name,
            link='/mail/view?model=%s&res_id=%s' % ('hr.job', job.id,),
            job_id=job.id,
            job_name=job.name or '',
            job_title=job.name or '',
            direct_sub_count=len(job.child_ids - job),
            indirect_sub_count=job.child_all_count,
        )


    # def _prepare_employee_data(self, employee):
    #     job = employee.sudo().job_id
    #     return dict(
    #         id=employee.id,
    #         name=employee.name,
    #         link='/mail/view?model=%s&res_id=%s' % ('hr.employee.public', employee.id,),
    #         job_id=job.id,
    #         job_name=job.name or '',
    #         job_title=employee.job_title or '',
    #         direct_sub_count=len(employee.child_ids - employee),
    #         indirect_sub_count=employee.child_all_count,
    #     )

    # @http.route('/hr/get_redirect_model', type='json', auth='user')
    # def get_redirect_model(self):
    #     if request.env['hr.employee'].check_access_rights('read', raise_exception=False):
    #         return 'hr.employee'
    #     return 'hr.employee.public'

    @http.route('/hr/get_org_job_chart', type='json', auth='user')
    def get_org_chart(self, job_id, **kw):

        job = self._check_job(job_id, **kw)
        if not job:  # to check
            return {
                'parents': [],
                'children': [],
            }

        # compute employee data for org chart
        ancestors, current = request.env['hr.job'].sudo(), job.sudo()
        while current.parent_id and len(ancestors) < self._managers_level+1 and current != current.parent_id:
            ancestors += current.parent_id
            current = current.parent_id

        values = dict(
            self=self._prepare_job_data(job),
            managers=[
                self._prepare_job_data(ancestor)
                for idx, ancestor in enumerate(ancestors)
                if idx < self._managers_level
            ],
            managers_more=len(ancestors) > self._managers_level,
            children=[self._prepare_job_data(child) for child in job.child_ids if child != job],
        )
        values['managers'].reverse()
        return values

    @http.route('/hr/get_job_subordinates', type='json', auth='user')
    def get_job_subordinates(self, job_id, subordinates_type=None, **kw):

        job = self._check_job(job_id, **kw)
        if not job:  # to check
            return {}

        if subordinates_type == 'direct':
            res = (job.child_ids - job).ids
        elif subordinates_type == 'indirect':
            res = (job.subordinate_ids - job.child_ids).ids
        else:
            res = job.subordinate_ids.ids

        return res
