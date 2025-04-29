from odoo import fields, models, api, _


class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    basic = fields.Many2one('ebspayroll.additional.element.types', string="Basic")
    housing = fields.Many2one('ebspayroll.additional.element.types', string="Housing")
    transportation = fields.Many2one('ebspayroll.additional.element.types', string="Transportation")
    social = fields.Many2one('ebspayroll.additional.element.types', string="Social")
    other = fields.Many2one('ebspayroll.additional.element.types', string="Other")
    mobile = fields.Many2one('ebspayroll.additional.element.types', string="Mobile")
    uniform = fields.Many2one('ebspayroll.additional.element.types', string="Uniform")
    fixed_overtime = fields.Many2one('ebspayroll.additional.element.types', string="Fixed Overtime")
    furniture_allowance = fields.Many2one('ebspayroll.additional.element.types', string="Furniture Allowance")
    ticket_allowance = fields.Many2one('ebspayroll.additional.element.types', string="Ticket Allowance")
    furniture_maintenance = fields.Many2one('ebspayroll.additional.element.types', string="Furniture Maintenance")

    @api.model
    def get_values(self):
        res = super(ResConfig, self).get_values()
        ebs_obj = self.env['ebspayroll.additional.element.types']
        basic = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.basic')
        housing = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.housing')
        transportation = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.transportation')
        social = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.social')
        other = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.other')
        mobile = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.mobile')
        uniform = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.uniform')
        fixed_overtime = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.fixed_overtime')
        furniture_allowance = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.furniture_allowance')
        ticket_allowance = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.ticket_allowance')
        furniture_maintenance = self.env['ir.config_parameter'].sudo().get_param('employee_promotion.furniture_maintenance')
        res.update(
            basic=ebs_obj.sudo().search([('id', '=', basic)]).id,
            housing=ebs_obj.sudo().search([('id', '=', housing)]).id,
            transportation=ebs_obj.sudo().search([('id', '=', transportation)]).id,
            social=ebs_obj.sudo().search([('id', '=', social)]).id,
            other=ebs_obj.sudo().search([('id', '=', other)]).id,
            mobile=ebs_obj.sudo().search([('id', '=', mobile)]).id,
            uniform=ebs_obj.sudo().search([('id', '=', uniform)]).id,
            fixed_overtime=ebs_obj.sudo().search([('id', '=', fixed_overtime)]).id,
            furniture_allowance=ebs_obj.sudo().search([('id', '=', furniture_allowance)]).id,
            ticket_allowance=ebs_obj.sudo().search([('id', '=', ticket_allowance)]).id,
            furniture_maintenance=ebs_obj.sudo().search([('id', '=', furniture_maintenance)]).id,
        )
        return res

    def set_values(self):
        super(ResConfig, self).set_values()
        self.env['ir.config_parameter'].set_param('employee_promotion.basic', self.basic.id)
        self.env['ir.config_parameter'].set_param('employee_promotion.housing', self.housing.id)
        self.env['ir.config_parameter'].set_param('employee_promotion.transportation', self.transportation.id)
        self.env['ir.config_parameter'].set_param('employee_promotion.social', self.social.id)
        self.env['ir.config_parameter'].set_param('employee_promotion.other', self.other.id)
        self.env['ir.config_parameter'].set_param('employee_promotion.mobile', self.mobile.id)
        self.env['ir.config_parameter'].set_param('employee_promotion.uniform', self.uniform.id)
        self.env['ir.config_parameter'].set_param('employee_promotion.fixed_overtime', self.fixed_overtime.id)
        self.env['ir.config_parameter'].set_param('employee_promotion.furniture_allowance', self.furniture_allowance.id)
        self.env['ir.config_parameter'].set_param('employee_promotion.ticket_allowance', self.ticket_allowance.id)
        self.env['ir.config_parameter'].set_param('employee_promotion.furniture_maintenance', self.furniture_maintenance.id)

