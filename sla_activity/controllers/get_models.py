# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class SlaActivity(http.Controller):
    @http.route("/GetModels/", auth="public", type="json", methods=["POST"])
    def get_models(self, **kwargs):
        params = request.httprequest.args.to_dict()
        language = params.get("lang") if params.get("lang") else False
        data = []

        models = request.env['ir.model'].sudo().search([
            ('model', 'in', ['hr.leave', 'approval.request'])
        ])
        if models:
            for model in models:
                model_name = model.name
                if language and language == "ar":
                    model_name = model.with_context(lang="ar_001").name
                name = ""
                if model.model_type == 'internal':
                    name = 'تخصصى'
                elif model.model_type == 'self_service':
                    name = 'ذاتى'
                data.append({"model": model.model,
                             "name": model_name,
                             "model_type": name
                             })

        related_models = request.env['dynamic.approval'].sudo().search([])
        if related_models:
            for related_model in related_models:
                model_name = related_model.model_id.name
                if language and language == "ar":
                    model_name = related_model.model_id.with_context(lang="ar_001").name
                name = ''
                if related_model.model_id.model_type == 'internal':
                    name = 'تخصصى'
                elif related_model.model_id.model_type == 'self_service':
                    name = 'ذاتى'
                data.append({"model": related_model.model_id.model,
                             "name": model_name,
                             "model_type": name
                             })
        return data
