from odoo import models, fields, api, _

class DocumentValidationWizard(models.TransientModel):
    _name = 'document.validation.wizard'
    _description = 'Validate In and Out documents'

    in_document_ids = fields.Many2many('ebs.crm.proposal.in.documents',string='In Documents')
    out_document_ids = fields.Many2many('ebs.crm.proposal.out.documents',string='Out Documents')
    in_document_count = fields.Integer()
    out_document_count = fields.Integer()

    @api.model
    def default_get(self, field_list):
        result = super(DocumentValidationWizard, self).default_get(field_list)
        result['in_document_ids'] = [(6,0,self._context.get('in_docs'))]
        result['out_document_ids'] = [(6,0,self._context.get('out_docs'))]
        result['in_document_count'] = len(self._context.get('in_docs'))
        result['out_document_count'] = len(self._context.get('out_docs'))
        return result

    def confirm_save(self):
        workflow_id = self.env['ebs.crm.proposal.workflow.line'].browse([self._context.get('active_id')])
        service = workflow_id.service_process_id
        context = {}
        in_docs = self.in_document_ids
        out_docs = self.out_document_ids
        for in_doc in in_docs:
            if in_doc.doc_type_id.is_individual:
                if service.service_order_type == 'employee':
                    in_doc.name.employee_id = service.employee_id and service.employee_id.id
                else:
                    in_doc.name.partner_id = service.partner_id and service.partner_id.id
            if in_doc.doc_type_id.is_services:
                in_doc.name.service_id = service.service_id and service.service_id.id
        for out_doc in out_docs:
            if out_doc.doc_type_id.is_individual:
                if service.service_order_type == 'employee':
                    out_doc.name.employee_id = service.employee_id and service.employee_id.id
                else:
                    out_doc.name.partner_id = service.partner_id and service.partner_id.id
            if out_doc.doc_type_id.is_services:
                out_doc.name.service_id = service.service_id and service.service_id.id
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'ebs.crm.service.process',
            'res_id': workflow_id.service_process_id.id,
            'target': 'current',

        }