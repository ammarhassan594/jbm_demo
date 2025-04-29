# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class DepartmentApi(http.Controller):
    @http.route("/GetDepartments/", auth="public", type="json", methods=["POST"])
    def get_departments(self, **kwargs):
        data = []
        departments = request.env['hr.department'].sudo().search([], order='sort_priority asc')
        if departments:
            for department in departments:
                data.append({
                    'id': department.id,
                    'name': department.with_context(lang="ar_001").name,
                    'parent_id': department.parent_id.id or None,
                    'parent_name': department.parent_id.with_context(lang="ar_001").name or None,
                    'department_path': department.complete_name
                })
        # data = departments.read(['name', 'parent_id'])
        return data
