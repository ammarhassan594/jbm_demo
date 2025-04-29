# -*- coding: utf-8 -*-
# from odoo import http


# class EbsWaseefLeaveAdvance(http.Controller):
#     @http.route('/ebs_waseef_leave_advance/ebs_waseef_leave_advance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ebs_waseef_leave_advance/ebs_waseef_leave_advance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ebs_waseef_leave_advance.listing', {
#             'root': '/ebs_waseef_leave_advance/ebs_waseef_leave_advance',
#             'objects': http.request.env['ebs_waseef_leave_advance.ebs_waseef_leave_advance'].search([]),
#         })

#     @http.route('/ebs_waseef_leave_advance/ebs_waseef_leave_advance/objects/<model("ebs_waseef_leave_advance.ebs_waseef_leave_advance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ebs_waseef_leave_advance.object', {
#             'object': obj
#         })
