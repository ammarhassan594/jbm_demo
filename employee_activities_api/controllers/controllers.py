# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class EmployeeActivitiesAPI(http.Controller):
    @http.route("/GetEmployeeActivities/", auth="public", type="json", methods=["POST"])
    def get_activities_employee(self, **kwargs):
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
                ], limit=1)
                if employee:
                    # user = employee.user_id if employee.user_id else False
                    mail_activities = request.env['mail.activity'].sudo().search([
                        ('user_id', '=', user.id),
                    ])
                    for activity in mail_activities:
                        if activity.res_model in ['hr.attendance']:
                            continue
                        request_url = activity.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        request_url += "/web" + "/#id=%s&view_type=form&model=%s" % (
                        activity.res_id, activity.res_model)
                        data.append({
                            'URL': request_url,
                            'display_name': activity.res_model_id.with_context(lang="ar_001").name if activity.res_model_id.name else '',
                            'date_deadline': activity.date_deadline if activity.date_deadline else '',
                            'create_date': activity.create_date if activity.create_date else '',
                            'summary': activity.summary if activity.summary else '',
                        })

        return data
