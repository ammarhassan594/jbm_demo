# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import base64


class InternalRegulationsApi(http.Controller):
    @http.route("/GetInternalRegulations/", auth="public", type="json", methods=["POST"])
    def get_internal_regulations(self, **kw):
        data = []
        params = request.httprequest.args.to_dict()
        if params.get("username"):
            username = params.get("username")
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            if user:
                employee = request.env['hr.employee'].sudo().search([
                    ('user_id', '=', user.id)
                ])
                print("employee", employee)
                # internal_regulations = request.env['internal.regulations'].sudo().search([])
                internal_regulations = employee.employee_procedure_ids
                if internal_regulations:
                    for reg in internal_regulations:
                        # for i in internal_regulation.attachments:
                        #     attachment.append({
                        #         'attachment':list(base64.standard_b64decode(i))
                        #
                        #     })
                        data.append({
                                     "id": reg.procedure_name_id.id,
                                     "name": reg.procedure_name_id.name if reg.procedure_name_id.name else None,
                                     "description": reg.procedure_name_id.description if reg.procedure_name_id.description else None,
                                     "valid_from_date": reg.procedure_name_id.date_from.strftime('%d/%m/%Y %H:%M:%S') if reg.procedure_name_id.date_from else None,
                                     "valid_to_date": reg.procedure_name_id.date_to.strftime('%d/%m/%Y %H:%M:%S') if reg.procedure_name_id.date_to else None,
                                     "has_attachment": reg.procedure_name_id.attachment and True or False
                                     # "attachments": [{
                                     #     f"{attachment.name or 'attachment'}":
                                     #         list(base64.standard_b64decode(attachment.datas))} for attachment in
                                     #     internal_regulations.attachments
                                     # ],
                                     # })
                                     # "attachment": base64.encodebytes(reg.attachment)
                                     })
                return data
            else:
                data = "Invalid user login"
                return data
        else:
            data = "Please send a username"
            return data

    @http.route("/GetInternalRegulationsAttachment/", auth="public", type="json", methods=["POST"])
    def get_internal_regulations_attachment(self, **kw):
        data = []

        params = request.httprequest.args.to_dict()
        internal_regulation_id = params.get("record_id")

        if internal_regulation_id:
            internal_regulation = request.env['internal.regulations'].sudo().browse(int(internal_regulation_id))
            if internal_regulation:
                data.append({
                    "attachment": internal_regulation.attachment if internal_regulation.attachment else None
                })

        else:
            internal_regulations = request.env['internal.regulations'].sudo().search([])

            for reg in internal_regulations:
                data.append({
                    "id": reg.id,
                    "attachment": reg.attachment if reg.attachment else None
                })

        return data
