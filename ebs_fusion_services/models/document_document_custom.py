from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class DocumentsCustom(models.Model):
    _inherit = 'documents.document'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self._context.get('service_order_type') == 'company':
            if not self._context.get('document_type_id'):

                return super(DocumentsCustom, self)._search(args=args, offset=offset, limit=limit, order=order,
                                                            count=count,
                                                            access_rights_uid=access_rights_uid)
            args = []
            related_partners = self.env['ebs.client.contact'].search(
                [('client_id', '=', self._context.get('partner'))]).mapped(
                'partner_id').ids
            related_partners.append(self._context.get('partner'))
            related_employees = self.env['hr.employee'].search(
                [('partner_parent_id', '=', self._context.get('partner'))]).ids
            args.append(('document_type_id', '=', self._context.get('document_type_id')))
            args.append(('|'))
            args.append(('employee_id','in',related_employees))
            args.append(('partner_id','in',related_partners))
            return super(DocumentsCustom, self)._search(args=args, offset=offset, limit=limit, order=order, count=count,
                                                        access_rights_uid=access_rights_uid)

        elif self._context.get('service_order_type') in ['employee', 'visitor', 'dependent']:
            args = []
            if self._context.get('document_type_id'):
                args.append(('document_type_id', '=', self._context.get('document_type_id')))
            if self._context.get('partner'):
                args.append(('partner_id', 'in', self._context.get('partner')))
            if self._context.get('employee'):
                args.append(('employee_id', 'in', self._context.get('employee')))
            return super(DocumentsCustom, self)._search(args=args, offset=offset, limit=limit, order=order, count=count,
                                                        access_rights_uid=access_rights_uid)

        else:
            return super(DocumentsCustom, self)._search(args=args, offset=offset, limit=limit, order=order, count=count,
                                                        access_rights_uid=access_rights_uid)

    proposal_id = fields.Many2one('ebs.crm.proposal',string='Proposal')
    service_id = fields.Many2one('ebs.crm.service', string='Service')
    service_process_id = fields.Many2one('ebs.crm.service.process', string='Service Orders')
    is_original = fields.Boolean('Original')
    is_user_owner = fields.Boolean(compute='compute_user')
    is_user_receiver = fields.Boolean(compute='compute_receiver')

    @api.model
    def create(self,vals):
        res = super(DocumentsCustom, self).create(vals)
        context = self.env.context
        doc_obj = ''
        if context.get('active_model') == 'ebs.crm.proposal.out.documents':
            doc_obj = self.env['ebs.crm.proposal.out.documents'].search([('id', '=', context.get('active_ids')[0])])
            service = doc_obj.service_process_id
            if doc_obj.doc_type_id.is_individual:
                if service.service_order_type == 'employee':
                    res.employee_id = service.employee_id and service.employee_id.id
                else:
                    res.partner_id = service.partner_id and service.partner_id.id
            if doc_obj.doc_type_id.is_services:
                res.service_id = service.service_id and service.service_id.id
        if context.get('active_model') == 'ebs.crm.proposal.in.documents':
            doc_obj = self.env['ebs.crm.proposal.in.documents'].search([('id', '=', context.get('active_ids')[0])])
            service = doc_obj.service_process_id
            if doc_obj.doc_type_id.is_individual:
                if service.service_order_type == 'employee':
                    res.employee_id = service.employee_id and service.employee_id.id
                else:
                    res.partner_id = service.partner_id and service.partner_id.id
            if doc_obj.doc_type_id.is_services:
                res.service_id = service.service_id and service.service_id.id
        if doc_obj:
            doc_obj.write({'name':res.id})
        return res

    def compute_user(self):
        for rec in self:
            rec.is_user_owner = False
            logs = self.env['ebs.transfer.document.log'].search([('document_id','=',self.id),
                                                                  ('sender','=',self.env.uid),
                                                                  ('state','=','pending')])
            if rec.owner_id.id == self.env.uid:
                rec.is_user_owner = True

    def compute_receiver(self):
        for rec in self:
            rec.is_user_receiver = False
            transfer_logs = self.env['ebs.transfer.document.log'].search([('document_id','=',self.id),
                                                                          ('receiver','=',self.env.uid),
                                                                          ('state','=','pending')])
            print(transfer_logs)
            if len(transfer_logs) > 0:
                rec.is_user_receiver = True
            print(rec.is_user_receiver,"@222222222222")

    def receive_doc(self):
        for rec in self:
            rec.owner_id = self.env.uid
            transfer_logs = self.env['ebs.transfer.document.log'].search([('document_id', '=', self.id),
                                                                          ('receiver', '=', self.env.uid),
                                                                          ('state', '=', 'pending')])
            transfer_logs.state = 'received'


    def action_show_transfer_log(self):
        self.ensure_one()
        action = self.env.ref('ebs_fusion_services.action_ebs_transfer_document_log').read()[0]
        action['context'] = {
            'default_document_id': self.id,
        }
        action['view_mode'] = 'tree'
        action['views'] = [(self.env.ref('ebs_fusion_services.view_ebs_transfer_document_log_tree').id, 'tree'),
                           (self.env.ref('ebs_fusion_services.view_ebs_transfer_document_log_form').id, 'form'),]
        action['target'] = 'self'
        return action


class EbsTransferDocumentLog(models.Model):
    _name = 'ebs.transfer.document.log'
    _description = 'Transfer Document Log'

    transfer_date = fields.Datetime('Transfer Date',default=datetime.today())
    sender = fields.Many2one('res.users','Sender')
    receiver = fields.Many2one('res.users', 'Receiver')
    state = fields.Selection([('pending','Pending'),('received','Received')],string='State')
    description = fields.Text('Description')
    document_id = fields.Many2one('documents.document','Document')


class EbsTransferDocument(models.Model):
    _name = 'ebs.transfer.document'
    _description = 'Transfer Document'

    transfer_date = fields.Datetime('Transfer Date', default=datetime.today())
    sender = fields.Many2one('res.users', 'Sender')
    receiver = fields.Many2one('res.users', 'Receiver')
    state = fields.Selection([('pending', 'Pending'), ('received', 'Received')], string='State')
    description = fields.Text('Description')
    document_id = fields.Many2one('documents.document', 'Document')


class ebsDocumentTypeInherit(models.Model):
    _inherit = 'ebs.document.type'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if 'service_process_id' in self._context:
            service_order_id = self.env['ebs.crm.service.process'].browse(self._context.get('service_process_id'))
            in_doc_ids = service_order_id.in_document_ids.mapped('doc_type_id').ids
            out_doc_ids = service_order_id.out_document_ids.mapped('doc_type_id').ids
            if self._context.get('in_docs'):
                args.append(('id', 'in', in_doc_ids))
            elif self._context.get('out_docs'):
                args.append(('id', 'in', out_doc_ids))
            else:
                args.append(('id', 'in', []))
        return super(ebsDocumentTypeInherit, self)._search(args=args, offset=offset, limit=limit, order=order, count=count,
                                               access_rights_uid=access_rights_uid)
