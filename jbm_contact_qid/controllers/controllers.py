# -*- coding: utf-8 -*-
# from odoo import http


# class JbmContactQid(http.Controller):
#     @http.route('/jbm_contact_qid/jbm_contact_qid', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/jbm_contact_qid/jbm_contact_qid/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('jbm_contact_qid.listing', {
#             'root': '/jbm_contact_qid/jbm_contact_qid',
#             'objects': http.request.env['jbm_contact_qid.jbm_contact_qid'].search([]),
#         })

#     @http.route('/jbm_contact_qid/jbm_contact_qid/objects/<model("jbm_contact_qid.jbm_contact_qid"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('jbm_contact_qid.object', {
#             'object': obj
#         })
