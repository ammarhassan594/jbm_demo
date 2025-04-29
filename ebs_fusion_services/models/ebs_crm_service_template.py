from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ebsCrmServiceTemplate(models.Model):
    _name = 'ebs.crm.service.template'
    _rec_name = 'name'
    _description = 'EBS CRM Service Template'

    name = fields.Char("Name", required=1)
    is_default = fields.Boolean('Is Default')
    workflow_lines = fields.One2many('ebs.crm.template.workflow', 'service_template_id', string='Workflows')
    service_id = fields.Many2one('ebs.crm.service', string='Service', required=1)
    status = fields.Selection([('draft', 'Draft'), ('ready', 'Ready')], string='Status', default='draft')
    workflow_type = fields.Selection([('online', 'Online'), ('manual', 'Manual')], string='Workflow Type')
    document_type_ids = fields.One2many('ebs.service.template.document.type', 'service_template_id',
                                        string='Document Types')
    days_to_complete = fields.Float(string='Days to complete')

    @api.constrains('is_default', 'service_id')
    def _check_values(self):
        for record in self:
            service_template_ids = self.search([('is_default', '=', True), ('service_id', '=', record.service_id.id)])
            if len(service_template_ids) > 1:
                raise ValidationError("There already exists a default template with this service")

    def fetch_workflows(self):
        self.status = 'ready'
        for rec in self:
            print(rec, "!!!rec")
            if rec.service_id:
                print("###service", rec.service_id)
                service = rec.service_id
                for type in service.document_type_ids:
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!mm")
                    document_type_id = self.env['ebs.service.template.document.type'].search(
                        [('service_template_id', '=', self.id),
                         ('document_type_id', '=', type.document_type_id.id)])
                    if not document_type_id:
                        document_type_id = self.env['ebs.service.template.document.type'].create({
                            'document_type_id': type.document_type_id.id,
                            'input': type.input,
                            'output': type.output,
                            'individual': type.individual,
                            'service': type.service,
                        })
                        print(document_type_id, "!!!!333333")
                        rec.write({'document_type_ids': [(4, document_type_id.id)]})
                    else:
                        document_type_id.write({
                            'input': type.input,
                            'output': type.output,
                            'individual': type.individual,
                            'service': type.service,
                        })
                if rec.workflow_type == 'online':
                    for line in service.workflow_lines:
                        if not line.service_phase == 'manual':
                            existing_id = self.env['ebs.crm.template.workflow'].search([
                                ('service_template_id', '=', rec.id),
                                ('activity_id', '=', line.activity_id.id)
                            ])
                            if not existing_id:
                                self.check_dependancy(line, rec)
                if rec.workflow_type == 'manual':
                    for line in service.workflow_lines:
                        if not line.service_phase == 'online':
                            existing_id = self.env['ebs.crm.template.workflow'].search([
                                ('service_template_id', '=', rec.id),
                                ('activity_id', '=', line.activity_id.id)
                            ])
                            if not existing_id:
                                self.check_dependancy(line, rec)
                if not rec.workflow_type:
                    for line in service.workflow_lines:
                        existing_id = self.env['ebs.crm.template.workflow'].search([
                            ('service_template_id', '=', rec.id),
                            ('activity_id', '=', line.activity_id.id)
                        ])
                        if not existing_id:
                            self.check_dependancy(line, rec)

    def check_dependancy(self, workflow_id, template_id):
        if workflow_id.dependant_workflow_ids:
            temp_workflow_ids = []
            for dep in workflow_id.dependant_workflow_ids:
                existing_id = self.env['ebs.crm.template.workflow'].search([
                    ('service_template_id', '=', template_id.id),
                    ('activity_id', '=', dep.activity_id.id)
                ])
                if existing_id:
                    if dep.service_phase == template_id.workflow_type or not dep.service_phase:
                        temp_workflow_ids.append(existing_id.id)
                else:
                    if dep.service_phase == template_id.workflow_type or not dep.service_phase:
                        temp_workflow_ids.append(
                            self.env['ebs.crm.template.workflow'].create({
                                'service_template_id': template_id.id,
                                'name': dep.id,
                                'activity_id': dep.activity_id.id,
                                'required_in_docs': [(6, 0, dep.required_in_docs.ids)],
                                'required_out_docs': [(6, 0, dep.required_out_docs.ids)],
                                'is_activity_required': dep.is_activity_required,
                                'workflow_days_to_complete': dep.workflow_days_to_complete,
                            }).id
                        )
            temp_workflow_id = self.env['ebs.crm.template.workflow'].create({
                'service_template_id': template_id.id,
                'name': workflow_id.id,
                'activity_id': workflow_id.activity_id.id,
                'required_in_docs': [(6, 0, workflow_id.required_in_docs.ids)],
                'required_out_docs': [(6, 0, workflow_id.required_out_docs.ids)],
                'is_activity_required': workflow_id.is_activity_required,
                'workflow_days_to_complete': workflow_id.workflow_days_to_complete,
            })
            for id in temp_workflow_ids:
                temp_workflow_id.write({'dependant_workflow_ids': [(4, id)]})
        else:
            existing_id = self.env['ebs.crm.template.workflow'].search([
                ('service_template_id', '=', template_id.id),
                ('activity_id', '=', workflow_id.activity_id.id)
            ])
            if not existing_id:
                self.env['ebs.crm.template.workflow'].create({
                    'service_template_id': template_id.id,
                    'name': workflow_id.id,
                    'activity_id': workflow_id.activity_id.id,
                    'required_in_docs': [(6, 0, workflow_id.required_in_docs.ids)],
                    'required_out_docs': [(6, 0, workflow_id.required_out_docs.ids)],
                    'is_activity_required': workflow_id.is_activity_required,
                    'workflow_days_to_complete': workflow_id.workflow_days_to_complete,
                })
            return True


class ebsCrmTemplateWorkflows(models.Model):
    _name = 'ebs.crm.template.workflow'
    _description = 'EBS CRM Template Workflow'
    _rec_name = 'name'

    name = fields.Many2one('ebs.crm.workflow', string='Process', required=0)
    sequence = fields.Integer(related='name.sequence', string='Sequence')
    activity_id = fields.Many2one('ebs.crm.service.activity', 'Activity')
    stage_id = fields.Many2one(related='name.stage_id', string='Service Stage', required=1)
    output = fields.Text(related='name.output', string='Output', required=1)

    responsible_user_id = fields.Many2one('ebs.services.user.group', 'Service User Group', )
    replacement_id = fields.Many2one(related='name.replacement_id', string='Replacement Department')

    service_phase = fields.Selection(related='name.service_phase', string='Type')
    service_template_id = fields.Many2one('ebs.crm.service.template', 'Service Template')
    dependant_workflow_ids = fields.Many2many('ebs.crm.template.workflow', 'service_template_workflow_dependant_rel',
                                              'workflow_id', 'dependant_id',
                                              string='Required Completed Workflows',
                                              domain="[('service_template_id','=',service_template_id)]")
    in_document_types = fields.Many2many('ebs.document.type', 'service_template_workflow_all_intype',
                                         compute='compute_document_types')
    out_document_types = fields.Many2many('ebs.document.type', 'service_template_workflow_all_outtype',
                                          compute='compute_document_types')
    required_in_docs = fields.Many2many('ebs.document.type', 'service_template_workflow_in_doctype_rel', 'workflow_id',
                                        'document_type_id', string='Required In Documents',
                                        domain="[('id','in',in_document_types)]")
    required_out_docs = fields.Many2many('ebs.document.type', 'service_template_workflow_out_doctype_rel',
                                         'workflow_id',
                                         'document_type_id', string='Required Out Documents',
                                         domain="[('id','in',out_document_types)]")
    is_activity_required = fields.Boolean('Is Activity Required')
    workflow_days_to_complete = fields.Float(string='Days to complete')

    @api.onchange('stage_id')
    def onchange_stage_id_(self):
        for rec in self:
            rec.activity_id = False
            if rec.stage_id:
                return {'domain': {
                    'activity_id': [('id', 'in', rec.stage_id.activity_ids.ids)],
                }}
            else:
                return {'domain': {
                    'activity_id': [(1, '=', 1)],
                }}

    @api.onchange('activity_id')
    def onchnage_activity_id(self):
        for rec in self:
            if rec.activity_id:
                rec.write({'required_in_docs': [(6, 0, rec.activity_id.in_documents.ids)],
                           'required_out_docs': [(6, 0, rec.activity_id.out_documents.ids)]
                           })
            else:
                rec.write({'required_in_docs': [(5, 0, 0)],
                           'required_out_docs': [(5, 0, 0)]
                           })

    def compute_document_types(self):
        for rec in self:
            in_document_type_ids = rec.service_template_id.document_type_ids.filtered(lambda l: l.input).mapped(
                'document_type_id')
            out_document_type_ids = rec.service_template_id.document_type_ids.filtered(lambda l: l.output).mapped(
                'document_type_id')
            rec.in_document_types = [(6, 0, in_document_type_ids.ids)]
            rec.out_document_types = [(6, 0, out_document_type_ids.ids)]


class ebsServiceDocumentTypes(models.Model):
    _name = 'ebs.service.template.document.type'
    _description = 'Ebs Service Template Document Type'

    document_type_id = fields.Many2one('ebs.document.type', 'Document Type')
    input = fields.Boolean('Input')
    output = fields.Boolean('Output')
    service = fields.Boolean('Service')
    individual = fields.Boolean('Individual')
    service_template_id = fields.Many2one('ebs.crm.service.template')
