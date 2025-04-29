# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.web.controllers.main import serialize_exception, \
    content_disposition
from odoo.http import request

class DownloadXlsReports(http.Controller):

    @http.route('/generate/custom_report/<model("custom.reports"):model>',
    type='http', auth="user")
    @serialize_exception

    def download_report_xls(self, model, **kw):
        # Method to download xls report without creating attachment
        data = model.generate_xlsx_report()
        if 'file_name' in request._context:
            filename = request._context.get('file_name')
        else:
            filename = 'Employee Report'
        if not data:
            return request.not_found()
        else:
            return request.make_response(
        data,
        [('Content-Type', 'application/octet-stream'),
        ('Content-Disposition', content_disposition(
        filename + '.xls'))])

# class I10nLbPayroll(http.Controller):
#     @http.route('/i10n_lb_payroll/i10n_lb_payroll/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/i10n_lb_payroll/i10n_lb_payroll/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('i10n_lb_payroll.listing', {
#             'root': '/i10n_lb_payroll/i10n_lb_payroll',
#             'objects': http.request.env['i10n_lb_payroll.i10n_lb_payroll'].search([]),
#         })

#     @http.route('/i10n_lb_payroll/i10n_lb_payroll/objects/<model("i10n_lb_payroll.i10n_lb_payroll"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('i10n_lb_payroll.object', {
#             'object': obj
#         })
