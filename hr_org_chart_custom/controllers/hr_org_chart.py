from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


class HrOrgChartController(http.Controller):
    _managers_level = 5

    def _check_employee(self, employee_id, **kw):
        if not employee_id:  # to check
            return None
        employee_id = int(employee_id)

        if 'allowed_company_ids' in request.env.context:
            cids = request.env.context['allowed_company_ids']
        else:
            cids = [request.env.company.id]

        Employee = request.env['hr.employee.public'].with_context(allowed_company_ids=cids)
        # check and raise
        if not Employee.check_access_rights('read', raise_exception=False):
            return None
        try:
            Employee.browse(employee_id).check_access_rule('read')
        except AccessError:
            return None
        else:
            return Employee.browse(employee_id)

    def _prepare_employee_data(self, employee):
        job = employee.sudo().job_id
        lang = request.env['res.users'].sudo().browse(request.uid).lang
        return dict(
            id=employee.id,
            name=employee.name,
            arabic_name=employee.arabic_name,
            link='/mail/view?model=%s&res_id=%s' % ('hr.employee.public', employee.id,),
            job_id=job.id,
            job_name=job.name or '',
            job_title=employee.job_title or '',
            direct_sub_count=len(employee.child_ids - employee),
            indirect_sub_count=employee.child_all_count,
            language=lang if lang else '',

        )

    @http.route('/hr_custom/get_org_chart', type='json', auth='user')
    def get_org_chart(self, employee_id, **kw):

        employee = self._check_employee(employee_id, **kw)
        if not employee:  # to check
            return {
                'managers': [],
                'children': [],
            }

        # compute employee data for org chart
        ancestors, current = request.env['hr.employee.public'].sudo(), employee.sudo()
        while current.parent_id and len(ancestors) < self._managers_level + 1 and current != current.parent_id:
            ancestors += current.parent_id
            current = current.parent_id

        values = dict(
            self=self._prepare_employee_data(employee),
            managers=[
                self._prepare_employee_data(ancestor)
                for idx, ancestor in enumerate(ancestors)
                if idx < self._managers_level
            ],
            managers_more=len(ancestors) > self._managers_level,
            children=[self._prepare_employee_data(child) for child in employee.child_ids if child != employee],
        )
        values['managers'].reverse()
        return values

