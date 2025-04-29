from odoo import api, fields, models, _
from datetime import datetime


class ebsLegalCase(models.Model):
    _name = 'ebs.legal.case'
    _description = 'EBS Legal Case'
    _order = "create_date desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Number', required=1)
    case_type = fields.Selection([('client', 'Client'), ('employee', 'Employee')], string='Type', default='client')
    fgh_as = fields.Selection([('victim', 'Victim'), ('accused', 'Accused')], string='FHG', default='victim')
    case_against = fields.Selection([('fme', 'FME'), ('other', 'Other Party')], string='Case Against')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Client',
                                 domain=[('is_customer', '=', True), ('is_company', '=', True),
                                         ('parent_id', '=', False)])
    employee_id = fields.Many2one('hr.employee', 'Employee')
    cases_received = fields.Boolean('Cases Received')
    cases_attended = fields.Boolean('Cases Attended')
    cases_not_attended = fields.Boolean('Cases Not Attended')
    cases_closed = fields.Boolean('Cases Closed')
    cases_not_resolved = fields.Boolean('Cases Not Resolved')
    cases_in_qatar = fields.Boolean('Cases In Qatar')
    location_case_qatar = fields.Text('Location of Case in Qatar')
    cases_outside_qatar = fields.Boolean('Cases Outside Qatar')
    cases_handled_by_qatar_law_firms = fields.Boolean('Cases handled by Qatar Law Firms')
    law_firms = fields.Many2one('ebs.legal.law.firm', 'Law Firm')
    cases_with_arbitrator = fields.Boolean('Cases with Arbitrator')
    cases_handled_by_inhouse_legal_team = fields.Boolean('Cases handled by Inhouse Legal Team')
    comments = fields.Text('Comments')
    state = fields.Selection([('draft', 'Draft'), ('ongoing', 'Ongoing'), ('closed', 'Closed')], default='draft',
                             string='State')
    document_ids = fields.One2many('documents.document', 'case_id', string='Police Report')
    document_count = fields.Integer(compute='_compute_document_count')
    activity_track_ids = fields.One2many('ebs.legal.activity.track', 'case_id', string='Activity Track')
    case_type_id = fields.Many2one(comodel_name='ebs.legal.case.type', string='Case Type')
    date = fields.Date('Date')
    date_closed = fields.Date('Date Closed')
    parent_id = fields.Many2one('ebs.legal.case', string="Related Case/Report")
    contact_id = fields.Many2one('res.partner', string="Contact", domain="[('parent_id', '=', partner_id)]")
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user.id, domain=lambda self: [
        ("groups_id", "in", [self.env.ref("ebs_fusion_legal.group_ebs_fusion_legal").id])])

    related_case_count = fields.Integer('Related Case', compute="compute_related_case")
    company_id = fields.Many2one('res.company', string="Company")
    accuser_ids = fields.One2many('ebs.case.contact', 'case_id', string="Accusers", domain=[('type', '=', 'accuser')])
    defender_ids = fields.One2many('ebs.case.contact', 'case_id', string="Defenders",
                                   domain=[('type', '=', 'defender')])

    purpose = fields.Many2one('ebs.legal.purpose')
    police_report_number = fields.Char('Police Report Number')
    public_prosecution_number = fields.Char('Public Prosecution Number')
    judgment = fields.Selection([
        ('innocence', 'Innocence'),
        ('other', 'Other'),
    ], string="Judgment")
    judgment_details = fields.Text('Judgment Details')
    type_id = fields.Many2one(comodel_name='ebs.legal.types', string='Type')
    litigation_degree_id = fields.Many2one(comodel_name='ebs.legal.litigation.degree', string='Degree Of Litigation')
    case_classification_id = fields.Many2one(comodel_name='ebs.legal.case.class', string='Case Classification',
                                             domain="[('case_type_id', '=', case_type_id)]")
    case_partial_classification_id = fields.Many2one(comodel_name='ebs.legal.case.partial.class',
                                                     string='Case Partial Classification')
    court_id = fields.Many2one('ebs.legal.court', 'Court')

    def compute_related_case(self):
        for rec in self:
            rec.related_case_count = self.env['ebs.legal.case'].search_count([('parent_id', '=', rec.id)])

    def action_related_case(self):
        action = self.env.ref('ebs_fusion_legal.action_ebs_legal_case').read([])[0]
        action['domain'] = [('parent_id', '=', self.id)]
        return action

    def create_new_case(self):
        self.ensure_one()
        accuser_ids = []
        defender_ids = []
        for accuser in self.accuser_ids:
            accuser_ids.append((0, 0, {
                'name': accuser.name,
                'type': accuser.type,
                'partner_id': accuser.partner_id.id,
                'related_number': accuser.related_number
            }))
        for defender in self.defender_ids:
            defender_ids.append((0, 0, {
                'name': defender.name,
                'type': defender.type,
                'partner_id': defender.partner_id.id,
                'related_number': defender.related_number
            }))
        return {
            'name': _('New Case'),
            'res_model': 'ebs.legal.case',
            'type': 'ir.actions.act_window',
            'views': [(False, 'form')],
            'view_mode': 'form',
            'context': {
                "default_fgh_as": self.fgh_as,
                "default_company_id": self.company_id.id,
                "default_partner_id": self.partner_id.id,
                "default_purpose": self.purpose.id,
                "default_law_firms": self.law_firms.id,
                "default_parent_id": self.id,
                "default_accuser_ids": accuser_ids,
                "default_defender_ids": defender_ids
            },
        }

    def _compute_document_count(self):
        read_group_var = self.env['documents.document'].read_group(
            [('case_id', 'in', self.ids)],
            fields=['case_id'],
            groupby=['case_id'])

        document_count_dict = dict((d['case_id'][0], d['case_id_count']) for d in read_group_var)
        for record in self:
            record.document_count = document_count_dict.get(record.id, 0)

    def action_see_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban')],
            'view_mode': 'kanban',
            'context': {
                "search_default_case_id": self.id,
                "default_case_id": self.id,
                "searchpanel_default_folder_id": False
            },
        }


class ebsLegalActivity(models.Model):
    _name = 'ebs.legal.activity.track'
    _description = 'EBS Legal Activity'

    date = fields.Datetime('Date', default=datetime.today())
    activity_type_id = fields.Many2one('ebs.legal.activity.type', string='Activity Type')
    user_id = fields.Many2one('res.users', string='User')
    description = fields.Char('Description')
    court = fields.Char('Court Name')
    case_id = fields.Many2one('ebs.legal.case', string='Case')
    law_firm_id = fields.Many2one(comodel_name='ebs.legal.law.firm', string='Law Firm')


class ebsLegalCourt(models.Model):
    _name = 'ebs.legal.court'
    _description = 'EBS Legal Court'

    name = fields.Char('Name')


class ebsLegalPurpose(models.Model):
    _name = 'ebs.legal.purpose'
    _description = 'EBS Legal Purpose'
    _rec_name = 'name'

    name = fields.Char('Name')
