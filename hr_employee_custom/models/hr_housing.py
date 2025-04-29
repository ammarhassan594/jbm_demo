from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class HrHousingType(models.Model):
    _name = 'hr.housing.type'
    _description = 'HR Housing Type'

    name = fields.Char('Types')
    nre = fields.Boolean(
        string='Non-Relative House',
        required=False, default=False)
    own = fields.Boolean(
        string='Owned House',
        required=False, default=False)
    rel = fields.Boolean(
        string='Relative House',
        required=False, default=False)
    ren = fields.Boolean(
        string='Rental House',
        required=False, default=False)


class HrHousingCategory(models.Model):
    _name = 'hr.housing.category'
    _description = 'HR Housing Category'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')


class CountryEmirate(models.Model):
    _name = 'res.country.emirate'
    _description = 'Res Country Emirate'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        required=True)
    city_code = fields.Char(related='country_id.code')


class CountryState(models.Model):
    _inherit = 'res.country.state'

    city_code = fields.Char(related='country_id.code')


class HrHousingAttach(models.Model):
    _name = 'hr.housing.attachment'
    _description = 'HR Housing Attachment'

    name = fields.Many2one('hr.housing.type', 'Name')

    attachment_ids = fields.Many2many(comodel_name="ir.attachment",
                                      relation="m2m_housing_attachments",
                                      column1="housing_id",
                                      column2="attachment_id",
                                      string="File"
                                      )
    related_housing = fields.Many2one('hr.housing', 'Related Housing')


class HrHousing(models.Model):
    _name = 'hr.housing'
    _description = 'Housing for employees'



    @api.onchange('housing_residential_type')
    def onchange_housing_residential_type(self):
        for rec in self:
            hrt = rec.housing_residential_type
            criteria = ()
            if hrt == 'nre':
                criteria = ('nre', '=', True)
            elif hrt == 'own':
                criteria = ('own', '=', True)
            elif hrt == 'rel':
                criteria = ('rel', '=', True)
            elif hrt == 'ren':
                criteria = ('ren', '=', True)

            if criteria != ():
                rec.attached_documents = False
                types = self.env['hr.housing.type'].search([criteria])
                if types:
                    result = []
                    for typee in types:
                        result.append((0, 0, {'name': typee.id, 'attachment_ids': None}))
                    rec.attached_documents = result

    @api.onchange('from_date')
    def onchange_from_date(self):
        for rec in self:
            from_date = rec.from_date
            if from_date:
                new_date = from_date + relativedelta(years=1)
                rec.to_date = new_date

    def update_default_attachments(self):
        for rec in self:
            current_types = rec.attached_documents.mapped('name')
            types = self.env['hr.housing.type'].search([('id', 'not in', current_types.ids)])
            if types:
                result = []
                for type in types:
                    result.append((0, 0, {'name': type.id, 'attachment_ids': None}))
                rec.attached_documents = result

    state = fields.Selection([('pending', 'Pending Approval'), ('approved', 'Approved'), ('refuse', 'Refused')],
                             default='pending',
                             string="Approval State")
    from_date = fields.Date('Contract Start Date')

    to_date = fields.Date('Contract End Date')
    housing_location = fields.Char("Location")
    city_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Emirate',
        required=False, domain="[('city_code', '=', 'AE')]")
    emirate_text = fields.Char(
        string='City',
        required=False)
    emirate_id = fields.Many2one(
        comodel_name='res.country.emirate',
        string='Emirate',
        required=False, domain="[('city_code', '=', 'AE')]")
    housing_residential_type = fields.Selection([('nre', 'Non-Relative House'),
                                                 ('own', 'Owned House'),
                                                 ('rel', 'Relative House'),
                                                 ('ren', 'Rental House'),
                                                 ], default='nre',
                                                string="Residential Type")
    housing_ownership = fields.Char("Ownership")
    housing_utility_bill = fields.Char("Utility Bill")
    attached_documents = fields.One2many('hr.housing.attachment', 'related_housing',
                                         string="Documents")
    related_declaration_form = fields.Many2one('documents.document')
    #                                        domain=lambda self: [('res_id', '=', self.employee_id.id), (
    # 'res_model', '=', self.employee_id._name)])
    related_lease_contract = fields.Many2one('documents.document')
    yearly_rent_value = fields.Float("Yearly Rent Value")
    tawtheeq_number = fields.Char("Tawtheeq Number")
    currency_id = fields.Many2one(related='employee_id.contract_id.currency_id')
    wage = fields.Monetary(related='employee_id.contract_id.wage')
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True)
    refuse_reason = fields.Text('Refuse Reason')
    housing_category_id = fields.Many2one(
        comodel_name='hr.housing.category',
        string='Housing Type',
        required=False)
    fusion_id = fields.Char(related='employee_id.fusion_id')

    def state_approve(self):
        self.refuse_reason = ""
        self.write({'state': 'approved'})
        msg = _('Housing ' + (self.housing_ownership if self.housing_ownership else '') + ' Approved')
        self.employee_id.message_post(body=msg)

    def state_pending(self):
        self.write({'state': 'pending'})

    def state_refuse(self):
        if self.refuse_reason:
            self.write({'state': 'refuse'})
            msg = _('Housing ' + (self.housing_ownership
                                  if self.housing_ownership else '') + ' Rejected. Rejection Reason: ' + (
                        self.refuse_reason if self.refuse_reason else ''))
            self.employee_id.message_post(body=msg)
        else:
            raise ValidationError('Must add refuse reason!')



    @api.constrains('from_date', 'to_date')
    def date_constrains(self):
        for rec in self:
            select_type = self.env['ir.config_parameter'].sudo()
            check_housing_duration = select_type.get_param('res.config.settings.check_housing_duration')
            if check_housing_duration:
                if rec.from_date and rec.to_date:
                    if rec.to_date != (rec.from_date + relativedelta(years=1)) and rec.to_date != (
                            rec.from_date + relativedelta(years=1) + relativedelta(days=-1)):
                        raise ValidationError(_('Housing Contract Duration must be approx. 1 year'))
