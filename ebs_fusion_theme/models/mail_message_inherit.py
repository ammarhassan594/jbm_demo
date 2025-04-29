from odoo import models, fields, api, _

class MaliMessages(models.Model):
    _inherit = 'mail.message'
    _description = 'Mail Messages'

    messages_read = fields.Boolean('Message Read')

    @api.model
    def create(self, vals):
        if self._context.get('clients_review') and self._context.get('default_parent_id'):
            default_parent_id = self._context.get('default_parent_id')
            new_context = dict(self.env.context).copy()
            new_context.pop('default_parent_id')
            self.env.context = new_context
            res = super(MaliMessages, self).create(vals)
            old_context = dict(self.env.context).copy()
            old_context.update({'default_parent_id': default_parent_id})
            self.env.context = old_context
        else:
            res = super(MaliMessages, self).create(vals)
        return res