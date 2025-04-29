# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    case_ref_no = fields.Char('Case Reference NO.')
    case_name = fields.Char('Case Name')
    case_qid = fields.Char('Case  QID')
    priority = fields.Selection(selection_add=[("2", "Very Urgent")], ondelete={'2': 'set default'})
    person_no = fields.Integer('PersonNO.')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    region = fields.Char('Region')
    rooms_no = fields.Integer('Rooms NO.')
    case_attachment_id = fields.Many2one('ir.attachment', string='Attachment')
    accommodation_api = fields.Boolean(default=False)
    
    # _sql_constraints = [
    #     ('case_ref_no_company_uniq', 'unique (case_ref_no,company_id)', 'The case reference number must be unique per company !')
    # ]

    