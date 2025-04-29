from odoo import api, fields, models, _

class WarningWizard(models.TransientModel):
    _name = "warning.wizard"
    _description = 'Warning Wizard'

    message = fields.Text(string="Message")

    @api.model
    def default_get(self, fields):
        res = super(WarningWizard, self).default_get(fields)
        res['message'] = self._context.get('message')
        return res


    def confirm_button(self):
        custom_method_name = self._context.get('method')
        model = self._context.get('model')
        object = self.env[model].browse(self._context.get('object_id'))
        kwargs = self._context.get('kwargs')
        if hasattr(object, custom_method_name):
            return getattr(object, custom_method_name)(**kwargs)
