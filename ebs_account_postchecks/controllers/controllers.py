# # -*- coding: utf-8 -*-
# from odoo import http
# from odoo.http import request
# from odoo.tools.translate import _
# from odoo.tools.config import config
# from odoo.exceptions import AccessDenied
# import json
# import base64
#
#
# class EbsCapstoneCrm(http.Controller):
#
#
# # @http.route('/api/country/get', type='http', auth='public', method=['GET'])
# # def get_country(self):
# #     auth_resp = self.check_auth()
# #     headers = [('Content-Type', 'application/json')]
# #     if auth_resp.get("status") == 'error':
# #         return request.make_response(json.dumps(auth_resp), headers=headers)
# #     country_json = []
# #     records = request.env['res.country'].sudo().search([])
# #     for record in records:
# #         country_json.append({'name': record.name,
# #                              'id': record.id})
# #
# #     data = {'status': "success", 'message': 'Countries List', 'data': country_json}
# #
# #     return request.make_response(json.dumps(data), headers=headers)
#
# # @http.route('/api/brandtype/get', type='http', auth='public', method=['GET'])
# # def get_brandtype(self):
# #     auth_resp = self.check_auth()
# #     headers = [('Content-Type', 'application/json')]
# #     if auth_resp.get("status") == 'error':
# #         return request.make_response(json.dumps(auth_resp), headers=headers)
# #     brandtype_json = []
# #     records = request.env['ebs.mod.brand.type'].sudo().search([])
# #     for record in records:
# #         brandtype_json.append({'name': record.name,
# #                                'id': record.id})
# #
# #     data = {'status': "success", 'message': 'Brand type List', 'data': brandtype_json}
# #
# #     return request.make_response(json.dumps(data), headers=headers)
#
# # @http.route('/api/establishments/get', type='http', auth='public', method=['GET'])
# # def get_establishments(self):
# #     auth_resp = self.check_auth()
# #     headers = [('Content-Type', 'application/json')]
# #     if auth_resp.get("status") == 'error':
# #         return request.make_response(json.dumps(auth_resp), headers=headers)
# #     establishments_json = []
# #     records = request.env['ebs.mod.contact.type.of.establishment'].sudo().search([])
# #     for record in records:
# #         establishments_json.append({'name': record.name,
# #                                     'id': record.id})
# #
# #     data = {'status': "success", 'message': 'Establishment type List', 'data': establishments_json}
# #
# #     return request.make_response(json.dumps(data), headers=headers)
#
# #     @http.route('/ebs_capstone_account/ebs_capstone_account/objects/', auth='public')
# #     def list(self, **kw):
# #         return http.request.render('ebs_capstone_account.listing', {
# #             'root': '/ebs_capstone_account/ebs_capstone_account',
# #             'objects': http.request.env['ebs_capstone_account.ebs_capstone_account'].search([]),
# #         })
#
# #     @http.route('/ebs_capstone_account/ebs_capstone_account/objects/<model("ebs_capstone_account.ebs_capstone_account"):obj>/', auth='public')
# #     def object(self, obj, **kw):
# #         return http.request.render('ebs_capstone_account.object', {
# #             'object': obj
# #         })
