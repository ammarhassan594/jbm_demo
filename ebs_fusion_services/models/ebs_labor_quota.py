from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import ValidationError


class LaborQuota(models.Model):
    _name = 'ebs.labor.quota'
    _description = 'EBS Labor Quota'
    _rec_name = 'app_no'

    partner_id = fields.Many2one('res.partner', 'Company/Client',
                                 domain=['|', ('company_partner', '=', True), ('is_customer', '=', True),
                                         ('is_company', '=', True)])
    app_no = fields.Char("Application Number")
    expiry_date = fields.Date("Expiry Date")
    app_date = fields.Date("Application Date")
    status = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('rejected', 'Rejected'),
                               ('partially_approved', 'Partially Approved')], string='Status', default='draft')

    labor_quota_line_id = fields.One2many('labor.quota.line', 'labor_id', string="Labor Quota Line")
    service_order_id = fields.Many2one('ebs.crm.service.process', "Service Order")
    vp_number = fields.Char('VP Number')

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if 'labor_option' in self._context and self._context.get('labor_option') != 'new':
            if self._context.get('labor_option') == 'manage':
                query = """ Select array_agg(id) as lq_id from ebs_labor_quota where partner_id=%s and expiry_date >= '%s' """ % (
                    self._context.get('client_id'), date.today().strftime("%Y-%m-%d"))
            if self._context.get('labor_option') == 'renew':
                query = """ Select array_agg(id) as lq_id from ebs_labor_quota where partner_id=%s and expiry_date < '%s' """ % (
                    self._context.get('client_id'), date.today().strftime("%Y-%m-%d"))

            self.env.cr.execute(query)
            query_result = self.env.cr.dictfetchall()
            res = query_result and query_result[0].get('lq_id')
            return res
        return super(LaborQuota, self)._search(args=args, offset=offset, limit=limit, order=order, count=count,
                                               access_rights_uid=access_rights_uid)


class LaborQuotaLine(models.Model):
    _name = 'labor.quota.line'
    _description = 'Labor Quota Line'
    _rec_name = 'ref_no'

    labor_id = fields.Many2one('ebs.labor.quota')
    app_no = fields.Char(related='labor_id.app_no')
    expiry_date = fields.Date(related="labor_id.expiry_date")
    app_date = fields.Date(related="labor_id.app_date")
    vp_number = fields.Char(related='labor_id.vp_number')
    partner_id = fields.Many2one(related="labor_id.partner_id", store=True)
    job_id = fields.Many2one('hr.job', "Job Title")
    nationality_id = fields.Many2one('res.country', "Nationality")

    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    ref_no = fields.Char("Reference Number")
    qty = fields.Integer("Quantity", default=1)
    qty_used = fields.Integer("Quantity Used", compute='compute_qty')
    qty_remaining = fields.Integer("Quantity Remaining", compute='compute_qty')
    qty_reserved = fields.Integer("Quantity Reserved")
    qty_reserved_proposal = fields.Integer("Quantity Reserved by Proposal", compute='compute_qty_reserved')
    subline_ids = fields.One2many('labor.quota.subline', 'line_id', string='Labor Quota Sublines')
    history_line_ids = fields.One2many('labor.quota.history.line', 'labor_quota_line_id', string='History')
    reserved_line_ids = fields.One2many('labor.quota.reserve.line', 'line_id', string='Reserved Lines')

    @api.depends('reserved_line_ids')
    def compute_qty_reserved(self):
        for rec in self:
            rec.qty_reserved_proposal = len(rec.reserved_line_ids)

    def compute_qty(self):
        for rec in self:
            qty_used = len(rec.subline_ids.filtered(lambda o: o.status in ['booked', 'updated']).ids)
            rec.qty_used = qty_used
            rec.qty_remaining = rec.qty - qty_used - rec.qty_reserved_proposal - rec.qty_reserved

    @api.model
    def create(self, vals):
        history_val = {'nationality_id': vals.get('nationality_id') if vals.get('nationality_id') else False,
                       'job_id': vals.get('job_id'),
                       'gender': vals.get('gender'),
                       'ref_no': vals.get('ref_no'),
                       'qty': str(vals.get('qty')),
                       }
        vals.update({'history_line_ids': [(0, 0, history_val)]})
        res = super(LaborQuotaLine, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('nationality_id') or vals.get('job_id') or vals.get('gender') or vals.get('ref_no') or vals.get(
                'qty'):
            history_val = {'nationality_id': vals.get('nationality_id').id if vals.get('nationality_id') else False,
                           'job_id': vals.get('job_id').id if vals.get('job_id') else False,
                           'gender': vals.get('gender') if vals.get('gender') else False,
                           'ref_no': vals.get('ref_no') if vals.get('ref_no') else False,
                           'qty': str(vals.get('qty')) if vals.get('qty') else '',
                           }
            vals.update({'history_line_ids': [(0, 0, history_val)]})
        res = super(LaborQuotaLine, self).write(vals)
        return res


class LaborQuotaSubline(models.Model):
    _name = 'labor.quota.subline'
    _description = 'Labor Quota SubLine'
    _rec_name = 'ref_no'

    line_id = fields.Many2one('labor.quota.line')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], related='line_id.gender', string='Gender')
    job_id = fields.Many2one('hr.job', related='line_id.job_id', string="Job Title")
    nationality_id = fields.Many2one('res.country', related='line_id.nationality_id', string="Nationality")
    status = fields.Selection([('available', 'Available'), ('booked', 'Booked'),
                               ('released', 'Released'), ('updated', 'Updated')], string='Status',
                              default='available')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    ref_no = fields.Char("Reference Number")
    contract_id = fields.Many2one('ebs.crm.proposal', string="Contract No.")

    def action_release_line(self):
        if self.status == 'booked':
            self.status = 'released'


class LaborQuotaReservedline(models.Model):
    _name = 'labor.quota.reserve.line'
    _description = 'Labor Quota Reserve Line'
    _rec_name = 'ref_no'

    line_id = fields.Many2one('labor.quota.line')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], related='line_id.gender', string='Gender')
    job_id = fields.Many2one('hr.job', related='line_id.job_id', string="Job Title")
    nationality_id = fields.Many2one('res.country', related='line_id.nationality_id', string="Nationality")

    employee_id = fields.Many2one('hr.employee', string='Employee')
    ref_no = fields.Char("Reference Number")
    contract_id = fields.Many2one('ebs.crm.proposal', string="Contract No.")
    lead_id = fields.Many2one('crm.lead', string="Lead")
    fos_fee_structure_id = fields.Many2one('ebs.proposal.fos.fee.structure')


class LaborQuotaHistoryLine(models.Model):
    _name = 'labor.quota.history.line'
    _description = 'Labor Quota History Line'

    labor_quota_line_id = fields.Many2one('labor.quota.line')
    date = fields.Date(string='Date', default=date.today())
    user = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    nationality_id = fields.Many2one('res.country', "Nationality")
    job_id = fields.Many2one('hr.job', "Job Title")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')

    ref_no = fields.Char("Reference Number")
    qty = fields.Char("Quantity")
