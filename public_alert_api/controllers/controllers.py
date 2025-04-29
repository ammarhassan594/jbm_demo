# -*- coding: utf-8 -*-
import base64
from datetime import datetime, date

from odoo import http
from odoo.http import request


def serialize_data(data):
    if not isinstance(data, dict):
        return {}
    new_data = {}
    for key, value in data.items():
        if isinstance(value, tuple):
            new_data[key] = value[1]
        elif isinstance(value, (datetime, date)):
            new_data[key] = value.strftime("%d/%m/%Y %H:%M:%S")
        else:
            new_data[key] = value if value else ''
    return new_data


class PublicAlertApi(http.Controller):
    @http.route("/GetPublicAlert/", auth="public", type="json", methods=["POST"])
    def get_public_alert(self, **kw):
        data = []
        result = []
        public_alerts = request.env['public.alert'].sudo().search([])
        if public_alerts:
            for public_alert in public_alerts:
                if public_alert.attachment:
                    result.append({"title": public_alert.title,
                                   "date": public_alert.date if public_alert.date else '',
                                   "description": public_alert.description,
                                   "attachment": base64.encodebytes(public_alert.attachment)
                                 # "attachment": list(base64.standard_b64decode(public_alert.attachment))
                                 })
                else:
                    result.append(public_alert.read(['title', 'date', 'description']))
            for alert_data in result:
                data.append(serialize_data(alert_data))
        return data
