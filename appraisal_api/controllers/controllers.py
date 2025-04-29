# -*- coding: utf-8 -*-

import base64
from datetime import datetime, date
from odoo import http, SUPERUSER_ID
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


class AppraisalApi(http.Controller):
    @http.route('/GetEmployeeAppraisal/', auth='public', type="json", methods=["POST"])
    def get_employee_appraisal(self, **kw):
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
                    appraisals = request.env['hr.appraisal'].sudo().search([
                        ('employee_id', '=', employee.id)
                    ])
                    if appraisals:
                        # for appraisal in appraisals:
                        #     data.append({
                        #         'employee_name': appraisal.employee_id.name,
                        #         'department_name': appraisal.department_id.name,
                        #         'appraisal_deadline': appraisal.date_close,
                        #     })
                        # data_appraisals = []
                        # for appraisal in appraisals:
                        #     data_appraisals.append(appraisal)
                        data_appraisals = appraisals.read([])
                        for d in data_appraisals:
                            data.append(serialize_data(d))
        return data

    @http.route('/GetEmployeeYearAppraisal/', auth='public', type="json", methods=["POST"])
    def get_employee_year_appraisal(self, **kw):
        data = {}
        username = False
        year = False
        params = request.httprequest.args.to_dict()
        if params.get("username"):
            username = params.get("username")
        if params.get('year'):
            year = params.get('year')
        if username:
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            employees = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
            if not employees:
                data = "There is No Employee By This Username "
        else:
            employees = request.env['hr.employee'].sudo().search([])
        for employee in employees:
            appraisals = request.env['hr.appraisal'].sudo().search([('employee_id', '=', employee.id),
                                                                    ('state', '=', 'done')])
            appraisal = request.env['hr.appraisal']
            if year and appraisals:
                appraisal = appraisals.filtered(lambda appraisal: appraisal.date_close.year == int(year)) \
                    .sorted('date_close')[-1] if \
                    appraisals.filtered(lambda appraisal: appraisal.date_close.year == int(year)) else False

            elif appraisals:
                appraisal = appraisals.sorted('date_close')[-1]
            if appraisal:
                # report_name = "taqat_hr_appraisal.action_report_jbm_appraisal_appraisal_a"
                # pdf = request.env.ref(report_name).with_user(SUPERUSER_ID)._render_qweb_pdf(res_ids=appraisal.id)[0]
                data.update({
                        'ID': appraisal.id,
                        'Year': appraisal.date_close.year if appraisal.date_close.year else None,
                        'overall_grade': appraisal.appraisal_overall_grade if appraisal.appraisal_overall_grade else None,
                        'employee_grade': appraisal.appraisal_current_grade if appraisal.appraisal_current_grade else None,
                        # 'Pdf report': base64.encodebytes(pdf),
                })
        if not data:
            data = "There Is No Appraisal For This Employee"
        return data

    @http.route('/GetAppraisalAttachment/', auth='public', type="json", methods=["POST"])
    def get_pdf_appraisal(self, **kw):
        data = []
        id = False
        params = request.httprequest.args.to_dict()
        if params.get("id"):
            id = params.get("id")
            if id:
                appraisals = request.env['hr.appraisal'].sudo().search([('id', '=', id)])
                if appraisals:
                    report_name = "taqat_hr_appraisal.action_report_jbm_appraisal_appraisal_a"
                    pdf = request.env.ref(report_name).with_user(SUPERUSER_ID)._render_qweb_pdf(res_ids=appraisals.id)[0]
                    data.append({'pdf_report': base64.encodebytes(pdf)})

        if not data:
            data = "There Is No Appraisal Data For This ID"
        return data

    @http.route('/GetAppraisalYears/', auth='public', type="json", methods=["POST"])
    def get_year_appraisal_by_employee(self, **kw):
        data = []
        username = False
        params = request.httprequest.args.to_dict()
        if params.get("username"):
            username = params.get("username")

        if username:
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            employees = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            if not employees:
                data = "There is No Employee By This Username "

            if employees:
                data_years = {}
                appraisals = request.env['hr.appraisal'].sudo().search([
                    ('employee_id', '=', employees.id),
                    ('state', '=', 'done')
                ], order='date_close ASC')
                if appraisals:
                    for appraisal in appraisals:
                        if appraisal.date_close and appraisal.date_close.year not in data_years:
                            data_years.update({'appraisal_year':appraisal.date_close.year})

                if data_years:
                    data.append(data_years)
        if not data:
            data = "There Is No Appraisal For This Employee"
        return data
