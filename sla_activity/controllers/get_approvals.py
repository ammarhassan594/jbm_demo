from odoo import http
from odoo.http import request


class SlaActivityApprovals(http.Controller):

    @http.route("/GetApprovals/", auth="public", type="json", methods=["POST"])
    def get_approvals(self, **kwargs):
        params = request.httprequest.args.to_dict()
        language = params.get("lang") if params.get("lang") else False

        data = []

        approvals = request.env['approval.category'].sudo().search([('is_sla', '=', True), ('sequence_code', '!=', False)])
        if approvals:
            for approval in approvals:
                name = approval.name
                if language and language == "ar":
                    name = approval.with_context(lang="ar_001").name
                if approval.sequence_code and approval.approval_type:
                    data.append({
                        'name': name,
                        'sequence_code': approval.sequence_code,
                        'approval_type': approval.approval_type,
                    })
                elif approval.sequence_code and not approval.approval_type:
                    data.append({
                        'name': name,
                        'sequence_code': approval.sequence_code,
                    })
                elif not approval.sequence_code and approval.approval_type:
                    data.append({
                        'name': name,
                        'approval_type': approval.approval_type,
                    })
                elif not approval.approval_type and not approval.sequence_code:
                    data.append({
                        'name': name,
                    })
        return data
