from odoo import http
from odoo.http import request


class SlaActivityLeaveType(http.Controller):

    @http.route("/GetLeaveTypes/", auth="public", type="json", methods=["POST"])
    def get_leave_types(self, **kwargs):
        params = request.httprequest.args.to_dict()
        language = params.get("lang") if params.get("lang") else False

        data = []
        leave_types = request.env['hr.leave.type'].sudo().search([])
        if leave_types:
            for leave_type in leave_types:
                name = leave_type.with_context(lang="ar_001").name if leave_type.with_context(lang="ar_001").name else leave_type.name
                data.append({
                    'id': leave_type.id,
                    'name': name,
                })
            # data = leave_types.read(['name'])
        return data