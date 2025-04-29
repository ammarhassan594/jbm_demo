from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ebsProposalFosFeeStructure(models.Model):
    _name = 'ebs.proposal.fos.fee.structure'
    _description = 'FOS Fees Structure'

    lead_id = fields.Many2one('crm.lead', string='Deal')
    contract_id = fields.Many2one('ebs.crm.proposal', string='Contract')
    number_employees = fields.Integer(string='No. Of Employees', default=1)
    job_position = fields.Many2one('hr.job', string='Job Position')
    visa_type = fields.Many2one('ebs.visa.type', string='Visa Type')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    nationality_id = fields.Many2one('res.country', string='Nationality')
    fee_person_month = fields.Float(string='Fee Per Person Per Month')
    labor_quota_id = fields.Many2one('ebs.labor.quota', string='Labor Quota')
    labor_quota_line_id = fields.Many2one('labor.quota.line', string='Labor Quota Line')
    reserved_deducted = fields.Boolean()
    status = fields.Selection([
        ('reserved', 'Reserved'),
        ('converted', 'Converted'),
        ('canceled', 'Canceled'),
    ], default="reserved", string='Status')

    @api.onchange('labor_quota_id')
    def get_labor_quota_id_domain(self):
        if self.lead_id:
            partner_id = self.lead_id.company_id.partner_id
        else:
            partner_id = self.contract_id.company_id.partner_id
        return {'domain': {'labor_quota_id': [('partner_id', '=', partner_id.id)]}}

    @api.onchange('labor_quota_id', 'nationality_id', 'job_position', 'gender')
    def onchange_labor_quota_id(self):
        for rec in self:
            if rec.labor_quota_id:
                lines = rec.labor_quota_id.labor_quota_line_id
                line_available = lines.filtered(lambda
                                                    o: o.nationality_id.id == rec.nationality_id.id and o.job_id.id == rec.job_position.id and o.gender == rec.gender and o.qty_remaining >= rec.number_employees)
                if not line_available:
                    raise UserError(_('This Labor Quota Is Not Available For This Conditions.'))

    def write(self, vals):
        if vals:
            if 'generate_button' not in self._context:
                labor_quota_id = vals.get('labor_quota_id') or self.labor_quota_id.id
                labor_quota = self.env['ebs.labor.quota'].sudo().search([('id', '=', labor_quota_id)])
                if labor_quota:
                    if labor_quota.labor_quota_line_id:

                        new_employee = vals.get('number_employees')
                        previous_employee = self.number_employees

                        if self.labor_quota_line_id and vals.get('number_employees'):
                            if new_employee < 0:
                                raise UserError(
                                    _('Employee Number can not be in minus.'))
                            if self.labor_quota_line_id.qty_remaining + previous_employee < new_employee:
                                raise UserError(
                                    _('There is no enough quantity labor quota line for this FOS fees structure.'))
                            else:

                                reserved_lines = self.labor_quota_line_id.reserved_line_ids.filtered(
                                    lambda l: l.lead_id.id == self.lead_id.id)
                                reserved_lines.unlink()
                                for count in range(new_employee):
                                    self.labor_quota_line_id.write(
                                        {'reserved_line_ids': [(0, 0, {'lead_id': self.lead_id.id,
                                                                       'fos_fee_structure_id': self.id})]})


                        else:
                            raise UserError(_('There is no matching labor quota line for this FOS fees structure.'))
                    else:
                        raise UserError(_('There is no labor quota line.'))
        res = super(ebsProposalFosFeeStructure, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        if vals:
            labor_quota = self.env['ebs.labor.quota'].sudo().search([('id', '=', vals.get('labor_quota_id'))])
            if labor_quota:
                if labor_quota.labor_quota_line_id:
                    subline = labor_quota.labor_quota_line_id.filtered(
                        lambda o: o.job_id.id == vals.get('job_position') and o.gender == vals.get(
                            'gender') and o.nationality_id.id == vals.get('nationality_id'))
                    if subline:
                        for rec in subline[0]:
                            if vals.get('number_employees') < 0:
                                raise UserError(
                                    _('Employee Number can not be in minus.'))
                            if rec.qty_remaining < vals.get('number_employees'):
                                raise UserError(
                                    _('There is no enough quantity labor quota line for this FOS fees structure.'))
                            elif rec.qty_remaining > 0:
                                for count in range(vals.get('number_employees')):
                                    rec.write({'reserved_line_ids': [(0, 0, {'lead_id': vals.get('lead_id')})]})
                                vals['labor_quota_line_id'] = rec.id
                    else:
                        raise UserError(_('There is no matching labor quota line for this FOS fees structure.'))
                else:
                    raise UserError(_('There is no labor quota line.'))

        res = super(ebsProposalFosFeeStructure, self).create(vals)
        return res

    def unlink(self):
        for rec in self:
            if rec.labor_quota_line_id:
                if rec.number_employees < 0:
                    raise UserError(
                        _('Employee Number can not be in minus.'))
                rest_of_qty = rec.labor_quota_line_id.qty_reserved_proposal - rec.number_employees
                reserved_lines = self.labor_quota_line_id.reserved_line_ids.filtered(
                    lambda l: l.lead_id.id == self.lead_id.id)
                reserved_lines.unlink()
        return super(ebsProposalFosFeeStructure, self).unlink()
