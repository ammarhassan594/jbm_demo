# -*- coding: utf-8 -*-
# from odoo import http


# class EbsHrDependentsFare(http.Controller):
#     @http.route('/ebs_hr_dependents_fare/ebs_hr_dependents_fare/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ebs_hr_dependents_fare/ebs_hr_dependents_fare/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ebs_hr_dependents_fare.listing', {
#             'root': '/ebs_hr_dependents_fare/ebs_hr_dependents_fare',
#             'objects': http.request.env['ebs_hr_dependents_fare.ebs_hr_dependents_fare'].search([]),
#         })

#     @http.route('/ebs_hr_dependents_fare/ebs_hr_dependents_fare/objects/<model("ebs_hr_dependents_fare.ebs_hr_dependents_fare"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ebs_hr_dependents_fare.object', {
#             'object': obj
#         })
