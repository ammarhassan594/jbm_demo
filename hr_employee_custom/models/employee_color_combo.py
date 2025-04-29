from odoo import fields, models, api


class EmployeeColorCombo(models.Model):
    _name = 'employee.color.combo'
    _description = 'Employee Color Combo'

    name = fields.Char('Color Class')
    # name = fields.Many2one(
    #     comodel_name='color.class',
    #     string='Color Class',
    #     required=True)
    nationality_id = fields.Many2one(
        comodel_name='res.country',
        string='Nationality',
        required=False)
    group_id = fields.Many2one(
        comodel_name='hr.contract.group',
        string='Group',
        required=False)
    subgroup_id = fields.Many2one(
        comodel_name='hr.contract.subgroup',
        string='Subgroup',
        required=False)
    employment_type_id = fields.Many2one(
        comodel_name='hr.contract.employment.type',
        string='Employment Type',
        required=False)
    leaver = fields.Boolean(
        string='Leaver',
        required=False, default=False)
    default_color_combo = fields.Boolean(
        string='Default Combo',
        required=False, default=False,
        help='If any condition was not fulfilled with the employee '
             'then we are set to default color combo,'
             ' if is boolean checked then apply that color combo')
