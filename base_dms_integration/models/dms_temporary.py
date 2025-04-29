from odoo import fields, models, api


class DmsTemporary(models.Model):
    _name = 'dms.temporary'
    _description = 'DMS Temporary Model for tracking sent records'

    dms_api_id = fields.Many2one('dms.integration', string='DMS Configuration')

    model_id = fields.Many2one('ir.model', string='Model',
                               readonly=True)
    res_model = fields.Char(string='Related Document Model',
                            readonly=True)
    report_id = fields.Many2one('ir.actions.report',
                                readonly=True)

    content_type_id = fields.Many2one('dms.content.type',
                                      string='Content type',
                                      readonly=True)

    api_method = fields.Selection([
        ('put', 'PUT'),
        ('post', 'POST')
    ],
        string='API Type',
        readonly=True)
    attachment = fields.Binary('Attachment')
    res_id = fields.Many2oneReference(
        string='Related Document ID',
        index=True,
        required=True,
        model_field='res_model'
    )
    file_name = fields.Char('File Name')
    processing_date = fields.Datetime()
    processed = fields.Boolean('Is Sent')
    user_id = fields.Many2one('res.users')
    response = fields.Html('Response Text')
    request = fields.Html('Request Text')
