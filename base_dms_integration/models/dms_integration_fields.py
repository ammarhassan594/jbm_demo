from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

from .dms_integration_mixin import evaluate_python_code


class DmsIntegrationFields(models.Model):
    _name = 'dms.fields'
    _description = 'DMS integration fields add fields which send to API.'

    # field_id = fields.Many2one('ir.model.fields', string='Field In Model',
    #                            help='Field In Selected Model', ondelete='cascade')
    api_field = fields.Char('API Field Name', required=True)
    send_type = fields.Selection([
        ('headers', 'Headers'),
        ('body', 'Body'),
        ('attachment', 'Attachment'),
    ], default='body')
    dms_api_id = fields.Many2one('dms.integration')
    model_id = fields.Many2one('ir.model', related='dms_api_id.model_id',
                               store=True, readonly=True)

    python_code = fields.Text('Python Expression',
                              default="""#To get a value from record must be write expression like this:\n#result = record.field_name\n""")
    file_name_expression = fields.Text(
        'File Name',
        default="""#To get a name of file from record must be write expression like this:\n#result = record.field_name\n#Or static value\n#result = "File Name"\n""",
    )

    # def _evaluate_python_expression(self):
    #     """Return the value of python expression"""
    #     res = self.env[self.model_id.model].sudo()
    #     try:
    #         localdict = {
    #             'time': time,
    #             'context_today': datetime.datetime.now,
    #             'user': self_sudo.env.user,
    #             'record': res,
    #         }
    #         safe_eval(self.python_code, localdict, mode="exec", nocopy=True)
    #         if localdict.get('result'):
    #             test = localdict.get('result')
    #         else:
    #             test = False
    #     except Exception as e:
    #         _logger.warning(e)
    #         test = False
    #     return test

    @api.constrains('python_code')
    def _check_python_code(self):
        for record in self:
            if record.model_id and record.python_code:
                test, message = \
                    evaluate_python_code(record=None, python_code=record.python_code,
                                         model_id=record.model_id, env=self.env)
                if test is None and message:
                    raise ValidationError(_('Wrong Python expression\n'
                                            f'{message}'))

    @api.constrains('file_name_expression')
    def _check_file_name_expression(self):
        for record in self:
            if record.send_type != 'attachment':
                continue
            if record.model_id and record.file_name_expression:
                test, message = \
                    evaluate_python_code(record=None, python_code=record.file_name_expression,
                                         model_id=record.model_id, env=self.env)
                if test is None and message:
                    raise ValidationError(_('Wrong File Name Expression\n'
                                            f'{message}'))
