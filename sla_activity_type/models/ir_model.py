from odoo import models, fields, api, _


class InheritIrModel(models.Model):
    _inherit = 'ir.model'

    apply_sla_activity = fields.Boolean()
    manager_expression = fields. \
        Text(string="Manager",
             default="""#Write your expression to get a manager\n#must be return one value like this:\n #result = record.field_name\n#You can use:\n #env: environment api\n#record: pointer to current record \n"""
             )
