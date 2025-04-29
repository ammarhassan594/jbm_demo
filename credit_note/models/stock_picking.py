from odoo import models, fields, api


class InheritStockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        object = super(InheritStockPicking, self).button_validate()
        self.user_id = self.env.user.id
        return object


    def action_print_delivery_note(self):
        return self.env.ref('credit_note.report_deliver_note_report_action').report_action(self)

