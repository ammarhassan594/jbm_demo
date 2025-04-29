import base64
import logging
import datetime
from odoo.tools.safe_eval import safe_eval, test_python_expr
from odoo import _, api, fields, models, tools, Command
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class DynamicEmailIntegrationDocument(models.Model):
    _name = 'dynamic.email.configuration'
    _description = 'Configuration of Dynamic Email'
    _order = 'id'

    _message = """  # Available variables:
                    # datetime: object
                    # dateutil: object
                    # time: object
                    # context_today
                    # user: current user when run condition.
                    # record: object containing the record as sales order.
                    # result = True or False\n\n\n\n
                """

    model_id = fields.Many2one(comodel_name='ir.model',
                               string='Model',
                               required=True,
                               ondelete='cascade', copy=False)

    name = fields.Char(
        string='Description',
        required=True,
        translate=True,
        copy=False
    )

    subject = fields.Char('Subject', translate=True, prefetch=True, help="Subject (placeholders may be used here)")
    report_name = fields.Char('Report Filename', translate=True, prefetch=True,
                              help="Name to use for the generated report file (may contain placeholders)\n"
                                   "The extension can be omitted and will then come from the report type.")

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.company, copy=False
    )

    active = fields.Boolean(
        default=True, copy=False
    )
    email_template_config = fields.Selection(
        selection=[('email_template', 'Email Templates'),
                   ('python_code', 'Python Code'),
                   ], string="Email Template Config", default=None, copy=False)
    email_template = fields.Text(default=_message, store=True, string="Email Template", copy=False)
    email_template_id = fields.Many2one(comodel_name='mail.template', copy=False, string="Email Template",
                                        domain="[('model_id', '=', model_id)]")
    attachment_or_report = fields.Selection(
        selection=[('report_template', 'Report Template'),
                   ('attachment', 'Attachments'),
                   ], string="Email Template Config", default=None, copy=False)
    report_template_id = fields.Many2one('ir.actions.report', 'Optional report to print and attach')
    attachment_ids = fields.Many2many('ir.attachment', 'dynamic_email_template_attachment_rel',
                                      'dynamic_email_template_id',
                                      'dynamic_attachment_id', 'Attachments',
                                      help="You may attach files to this template, to be added to all "
                                           "emails created from this template")

    action_field_id = fields.Many2one('ir.model.fields', domain="[('model_id', '=', model_id)]")
    action_field_value = fields.Char(string="Value")
    action_field_selection_id = fields.Many2one("models.selection.fields", "Value",
                                                domain="[('field_id', '=', action_field_id)]")
    field_ttype = fields.Selection(
        selection=[('selection', 'Selection'),
                   ('char', 'Char'),
                   ('integer', 'Integer'),
                   ('float', 'Float'),
                   ('many2one', 'Many2one'),
                   ('text', 'Text'),
                   ('monetary', 'Monetary'),
                   ('boolean', 'Boolean'),
                   ('date', 'Date'),
                   ('datetime', 'DateTime'),
                   ], string="Field Type",  copy=False)

    model = fields.Char(
        related='model_id.model',
        index=True,
        store=True,
        copy=False
    )

    email_approval_condition_ids = fields.One2many(
        comodel_name='dynamic.approval.email.condition',
        inverse_name='email_config_id',
        string='Conditions',
        copy=False,
    )
    from_email_config = fields.Selection(
        selection=[('manually', 'Manually'),
                   ('outgoing_mail_server', 'OutGoing Mail Server'),
                   ('python_code', 'Python Code'),
                   ], string="From Email Config", default=None, copy=False)
    outgoing_mail_server_id = fields.Many2one(comodel_name='ir.mail_server', copy=False)
    from_email_python_code = fields.Text(string="Python Code", copy=False)
    from_email = fields.Char(copy=False, string="From Email")

    to_email_config = fields.Selection(
        selection=[('manually', 'Manually'), 
                   ('python_code', 'Python Code'),
                   ('records', 'Records'),
                   ], string="TO Email Config", default=None, copy=False)
    to_email_python_code = fields.Text(string="Python Code", copy=False)
    to_email_python_code_records = fields.Text(string="Python Code", copy=False)
    to_email = fields.Char(copy=False, string="To Email")

    email_cc_config = fields.Selection(
        selection=[('manually', 'Manually'), ('python_code', 'Python Code'),
                   ], string="Email CC Config", default=None, copy=False)
    email_cc_python_code = fields.Text(string="Python Code", copy=False)
    email_cc = fields.Char(copy=False, string="Email cc")
    res_id = fields.Integer("Res Id")

    @api.onchange('action_field_id')
    def _onchange_action_field_id(self):
        if self.action_field_id.ttype == 'selection':
            self.field_ttype = 'selection'
        elif self.action_field_id.ttype == 'char':
            self.field_ttype = 'char'
        elif self.action_field_id.ttype == 'integer':
            self.field_ttype = 'integer'
        elif self.action_field_id.ttype == 'many2one':
            self.field_ttype = 'many2one'
        elif self.action_field_id.ttype == 'monetary':
            self.field_ttype = 'monetary'
        elif self.action_field_id.ttype == 'boolean':
            self.field_ttype = 'boolean'
        elif self.action_field_id.ttype == 'float':
            self.field_ttype = 'float'
        elif self.action_field_id.ttype == 'text':
            self.field_ttype = 'text'
        elif self.action_field_id.ttype == 'date':
            self.field_ttype = 'date'
        elif self.action_field_id.ttype == 'datetime':
            self.field_ttype = 'datetime'
        if self.action_field_id and self.action_field_id.ttype == 'selection':
            name = self.action_field_id.selection_ids.mapped('display_name')
            value_list = self.action_field_id.selection_ids.mapped('value')
            for i in range(0, len(name)):
                field_id = self.action_field_id.id
                key = value_list[i]
                value = name[i]
                self._cr.execute("""SELECT msp.id
                                    FROM models_selection_fields msp
                                    WHERE msp.field_id = %s and msp.key = %s and msp.value = %s  """,
                                 [field_id, key, value])
                to_models_selection_fields_ids = self._cr.dictfetchall()
                if not to_models_selection_fields_ids:
                    cr = self.env.cr

                    # Define your SQL query to insert a new record into res_partner
                    sql = """
                                INSERT INTO models_selection_fields (field_id, key, value ,create_uid,create_date)
                                VALUES (%s, %s, %s,%s,%s)                            """

                    # Execute the SQL query
                    cr.execute(sql, (
                    field_id, key, value, self.env.user.id, fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    @api.onchange('from_email_python_code')
    def onchange_model_from_email_python_code(self):
        for model in self:
            if model.from_email_python_code:
                if not model.model_id and model.from_email_python_code:
                    raise UserError("Select Model")
                model._is_condition_matched_python_code(python_code='from_email_python_code')

    @api.onchange('outgoing_mail_server_id')
    def onchange_model_outgoing_mail_server_id(self):
        for model in self:
            if model.from_email_config == 'outgoing_mail_server' and model.outgoing_mail_server_id:
                self.write({'from_email': model.outgoing_mail_server_id.smtp_user})

    @api.onchange('to_email_python_code')
    def onchange_model_to_email_python_code(self):
        for model in self:
            if model.to_email_python_code:
                if not model.model_id and model.to_email_python_code:
                    raise UserError("Select Model")
                model._is_condition_matched_python_code(python_code='to_email_python_code')

    @api.onchange('email_cc_python_code')
    def onchange_model_email_cc_python_code(self):
        for model in self:
            if model.email_cc_python_code:
                if not model.model_id:
                    raise UserError("Select Model")
                model._is_condition_matched_python_code(python_code='email_cc_python_code')

    @api.constrains('from_email_python_code')
    def _check_python_code(self):
        for action in self.sudo().filtered('from_email_python_code'):
            msg = test_python_expr(expr=action.from_email_python_code.strip(), mode="exec")
            if msg:
                raise UserError(msg)

    def _is_condition_matched_python_code(self, python_code):
        """ return true / false based on calculation type """
        self.ensure_one()
        dict_data = {'self': self, 'user_obj': self.env.user}
        try:
            if python_code == 'from_email_python_code':
                if self.from_email_python_code:
                    exec(self.from_email_python_code, dict_data)
                    if dict_data.get('result', False):
                        self.write({'from_email': dict_data['result']})
                else:
                    raise UserError(_("There is no lines for execute!!!"))
            elif python_code == 'to_email_python_code':
                if self.to_email_python_code:
                    exec(self.to_email_python_code, dict_data)
                    if dict_data.get('result', False):
                        self.write({'to_email': dict_data['result']})
                else:
                    raise UserError(_("There is no lines for execute!!!"))
            elif python_code == 'email_cc_python_code':
                if self.email_cc_python_code:
                    exec(self.email_cc_python_code, dict_data)
                    if dict_data.get('result', False):
                        self.write({'email_cc': dict_data['result']})
                else:
                    raise UserError(_("There is no lines for execute!!!"))
        except Exception as exception:
            raise UserError('{}'.format(exception))
        return True

    def create_report_attachment(self,records):
        attachments = []
        report_name = self.report_template_id.name + records.name
        report = self.report_template_id
        report_service = report.report_name

        if report.report_type in ['qweb-html', 'qweb-pdf']:
            result, report_format = self.env['ir.actions.report']._render_qweb_pdf(report, records.ids)
        else:
            res = self.env['ir.actions.report']._render(report, records.ids)
            if not res:
                raise UserError(_('Unsupported report type %s found.', report.report_type))
            result, report_format = res

        # TODO in trunk, change return format to binary to match message_post expected format
        result = base64.b64encode(result)
        if not report_name:
            report_name = 'report.' + report_service
        ext = "." + report_format
        if not report_name.endswith(ext):
            report_name += ext
        attachments.append((report_name, result))
        a, b = attachments[0]
        attachment_data = {
            'name': a,
            'datas': b,
            'type': 'binary',
            'res_model': 'mail.message',
            'res_id': records.id,
        }
        return self.env['ir.attachment'].create(attachment_data)

    def is_matched_approval(self, res):
        """ return True / False based on approval match record condition """
        self.ensure_one()
        for condition in self.email_approval_condition_ids:
            if not condition.is_condition_matched(res=res):
                return False
        return True

    def get_email_vals(self,records):
        dynamic_email_configuration_id = self
        if dynamic_email_configuration_id.to_email_config in ['manually','python_code'] and dynamic_email_configuration_id.to_email:
            email_to = dynamic_email_configuration_id.to_email
        elif dynamic_email_configuration_id.to_email_config == 'records':
            python_code = dynamic_email_configuration_id.to_email_python_code_records.split('.')
            email_to = records
            for i in python_code[1:]:
                email_to = email_to.__getitem__(i)
                if email_to:
                    pass
                else:
                    email_to = False
        email_values = {
            'email_from': dynamic_email_configuration_id.from_email,
            'subject': dynamic_email_configuration_id.subject,
            'email_to': email_to,
            'email_cc': dynamic_email_configuration_id.email_cc,
            'auto_delete': False,
            'model': records._name,
            'res_id': records.id,
        }
        if dynamic_email_configuration_id.attachment_or_report == 'report_template':
            if not dynamic_email_configuration_id.email_template_id.report_template or dynamic_email_configuration_id.email_template_config == 'python_code':
                attachment_ids = dynamic_email_configuration_id.sudo().create_report_attachment(records)
                if attachment_ids:
                    email_values.update({'attachment_ids': attachment_ids.ids})
        elif dynamic_email_configuration_id.attachment_or_report == 'attachment':
            if dynamic_email_configuration_id.attachment_ids:
                email_values.update({'attachment_ids': dynamic_email_configuration_id.attachment_ids.ids})

        if dynamic_email_configuration_id.email_template_config == 'python_code':
            dict_data = {'self': dynamic_email_configuration_id, 'user_obj': self.env.user}
            exec(dynamic_email_configuration_id.email_template, dict_data)
            if dict_data.get('result', False):
                body = dict_data['result']
            else:
                body = None
            msg = self.env['mail.message'].sudo().new(dict(body=body))
            template_ctx = {
                'message': msg,
                'company': self.env.company,
            }
            body_html = self.env['ir.qweb']._render('mail.mail_notification_light', template_ctx,
                                                    minimal_qcontext=True)
            body_html = self.env['mail.render.mixin']._replace_local_links(body_html)
            email_values.update({
                'body_html': body_html,
                'body': body,
            })
        return email_values


class ModelsSelectionFields(models.Model):
    _name = 'models.selection.fields'
    _rec_name = 'value'

    field_id = fields.Many2one('ir.model.fields')
    key = fields.Char("Key")
    value = fields.Char("Value")


class BaseModel(models.BaseModel):
    _inherit = 'base'

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        records_ids = super().create(vals_list)
        for records in records_ids:
            if records:
                dynamic_email_configuration_ids = self.env['dynamic.email.configuration'].sudo().search([('model_id', '=', records._name)])
                if dynamic_email_configuration_ids:
                    for dynamic_email_configuration_id in dynamic_email_configuration_ids:
                        dynamic_email_configuration_id.res_id = records.id
                        if dynamic_email_configuration_id.field_ttype == 'selection':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,dynamic_email_configuration_id.action_field_id.name) and getattr(records,dynamic_email_configuration_id.action_field_id.name) == dynamic_email_configuration_id.action_field_selection_id.key:
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id, force_send=True, email_values=email_values,email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()

                        elif dynamic_email_configuration_id.field_ttype == 'many2one':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,dynamic_email_configuration_id.action_field_id.name) and getattr(records,dynamic_email_configuration_id.action_field_id.name).name == dynamic_email_configuration_id.action_field_value:
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                        elif dynamic_email_configuration_id.field_ttype == 'monetary':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,dynamic_email_configuration_id.action_field_id.name) and getattr(records,
                                    dynamic_email_configuration_id.action_field_id.name) == float(dynamic_email_configuration_id.action_field_value):
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                        elif dynamic_email_configuration_id.field_ttype == 'float':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,dynamic_email_configuration_id.action_field_id.name) and getattr(records,
                                    dynamic_email_configuration_id.action_field_id.name) == float(dynamic_email_configuration_id.action_field_value):
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)

                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                        elif dynamic_email_configuration_id.field_ttype == 'integer':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,dynamic_email_configuration_id.action_field_id.name) and getattr(records,
                                    dynamic_email_configuration_id.action_field_id.name) == float(dynamic_email_configuration_id.action_field_value):
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                        elif dynamic_email_configuration_id.field_ttype == 'boolean':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,dynamic_email_configuration_id.action_field_id.name) and getattr(records,
                                    dynamic_email_configuration_id.action_field_id.name) == bool(dynamic_email_configuration_id.action_field_value):
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                        elif dynamic_email_configuration_id.field_ttype == 'char':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,dynamic_email_configuration_id.action_field_id.name) and getattr(records,
                                    dynamic_email_configuration_id.action_field_id.name) == dynamic_email_configuration_id.action_field_value:
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                        elif dynamic_email_configuration_id.field_ttype == 'text':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,dynamic_email_configuration_id.action_field_id.name) and getattr(records,
                                    dynamic_email_configuration_id.action_field_id.name) == dynamic_email_configuration_id.action_field_value:
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
        return records_ids

    def write(self, vals):
        res = super().write(vals)
        for records in self:
            if records and 'dynamic.email.configuration' in self.env['ir.model'].sudo().search([]).mapped('model'):
                dynamic_email_configuration_ids = self.env['dynamic.email.configuration'].sudo().search(
                    [('model_id', '=', records._name)])
                if dynamic_email_configuration_ids:
                    for dynamic_email_configuration_id in dynamic_email_configuration_ids:
                        dynamic_email_configuration_id.res_id = records.id
                        if dynamic_email_configuration_id.field_ttype == 'selection':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,
                                                                                          dynamic_email_configuration_id.action_field_id.name) and getattr(
                                    records,
                                    dynamic_email_configuration_id.action_field_id.name) == dynamic_email_configuration_id.action_field_selection_id.key:
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()

                        elif dynamic_email_configuration_id.field_ttype == 'many2one':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,
                                                                                          dynamic_email_configuration_id.action_field_id.name) and getattr(
                                    records,
                                    dynamic_email_configuration_id.action_field_id.name).name == dynamic_email_configuration_id.action_field_value:
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                        elif dynamic_email_configuration_id.field_ttype == 'monetary':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,dynamic_email_configuration_id.action_field_id.name) and getattr(
                                    records,dynamic_email_configuration_id.action_field_id.name) == float(dynamic_email_configuration_id.action_field_value):
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                        elif dynamic_email_configuration_id.field_ttype == 'float':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,
                                                                                          dynamic_email_configuration_id.action_field_id.name) and getattr(
                                    records,dynamic_email_configuration_id.action_field_id.name) == float(
                                dynamic_email_configuration_id.action_field_value):
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)

                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                        elif dynamic_email_configuration_id.field_ttype == 'integer':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,
                                                                                          dynamic_email_configuration_id.action_field_id.name) and getattr(
                                    records,
                                    dynamic_email_configuration_id.action_field_id.name) == float(
                                dynamic_email_configuration_id.action_field_value):
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                        elif dynamic_email_configuration_id.field_ttype == 'boolean':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,
                                                                                          dynamic_email_configuration_id.action_field_id.name) and getattr(
                                    records,
                                    dynamic_email_configuration_id.action_field_id.name) == bool(
                                dynamic_email_configuration_id.action_field_value):
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                        elif dynamic_email_configuration_id.field_ttype == 'char':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,
                                                                                          dynamic_email_configuration_id.action_field_id.name) and getattr(
                                    records,
                                    dynamic_email_configuration_id.action_field_id.name) == dynamic_email_configuration_id.action_field_value:
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                        elif dynamic_email_configuration_id.field_ttype == 'text':
                            if dynamic_email_configuration_id.action_field_id and hasattr(records,
                                                                                          dynamic_email_configuration_id.action_field_id.name) and getattr(
                                    records,
                                    dynamic_email_configuration_id.action_field_id.name) == dynamic_email_configuration_id.action_field_value:
                                if not dynamic_email_configuration_id.email_approval_condition_ids:
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()
                                elif dynamic_email_configuration_id.is_matched_approval(records):
                                    email_values = dynamic_email_configuration_id.get_email_vals(records)
                                    if dynamic_email_configuration_id.email_template_config == 'email_template':
                                        dynamic_email_configuration_id.email_template_id.sudo().send_mail(self.env.user.id,
                                                                                                          force_send=True,
                                                                                                          email_values=email_values,
                                                                                                          email_layout_xmlid='mail.mail_notification_light')
                                    else:
                                        self.env['mail.mail'].with_user(self.env.user).create(email_values).send()

        return res
