from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
import random


class ebsDocumentType(models.Model):
    _name = 'ebs.document.type'
    _description = 'EBS Document Type'
    _rec_name = 'name'

    name = fields.Char('Name')
    view_sequence = fields.Integer(string='Sequence Number', store=True)
    name_arabic = fields.Char('Arabic Name')
    document_categ_id = fields.Many2one(comodel_name="ebs.document.category", string="Document Category")
    description = fields.Char('Description')
    is_individual = fields.Boolean("Related To Partner")
    is_services = fields.Boolean("Related To Service")
    is_input_document = fields.Boolean("Input")
    is_output_document = fields.Boolean("Output")
    folder_ids = fields.Many2one('documents.folder', string='Workspace')
    image_attachment_id = fields.Many2one('ir.attachment', string='Image Attachment')
    extra_field_ids = fields.Many2many('ir.model.fields', string="Extra Field",
                                       domain=[('model', '=', 'documents.document')])
    abbreviation = fields.Char(string="Abbreviation")
    seq_req = fields.Boolean('Sequence Required')
    sequence = fields.Many2one('ir.sequence', string="Sequence")
    show_ar_file = fields.Boolean(string="Show Arabic File")
    visa_type = fields.Many2one('ebs.visa.type', string='Visa Type')
    meta_data_template = fields.Selection([('QID', 'QID'), ('Passport', 'Passport'),
                                           ('Commercial Registration (CR) Application',
                                            'Commercial Registration (CR) Application'),
                                           ('Commercial License', 'Trade License'),
                                           ('Establishment Card', 'Establishment Card'),
                                           ('Tax Card', 'Tax Card'),
                                           ('articles of association', 'Articles of Association'),
                                           ('Visa', 'Visa'),
                                           ('Foreign AOA', 'Foreign AOA'),
                                           ('Foreign CR', 'Foreign CR'),
                                           ('Foreign POA', 'Foreign POA'),
                                           ('Loan Agreement', 'Loan Agreement'),
                                           ('Shareholder Agreement', 'Shareholder Agreement'),
                                           ('Lease Agreement', 'Lease Agreement'),
                                           ('Power of Attorney', 'Power of Attorney'),
                                           ('E-Contract', 'E-Contract'),
                                           ],
                                          string='Metadata Template')
    is_agreement = fields.Boolean('Agreement')
    default_folder_ids = fields.One2many(comodel_name='ebs.document.type.folder', inverse_name='doc_type_id',
                                         string='Default Folder Details')

    _sql_constraints = [
        ('abbreviation_unique', 'unique (abbreviation)', "A Document Type With This Abbreviation Already Exists."),
        ('metadata_template_unique', 'unique (meta_data_template)',
         "A Document Type With This Metadata Template Already Exists."),
    ]

    @api.model
    def create(self, vals):
        seq_req = vals['seq_req']
        if seq_req:
            vals.update({'sequence': self.sudo()._create_sequence(vals).id})
        return super(ebsDocumentType, self).create(vals)

    def write(self, vals):
        if 'abbreviation' in vals or 'seq_req' in vals:
            if vals.get('seq_req') or self.seq_req:
                seq = vals.get('abbreviation') or self.abbreviation
                if seq:
                    sequence = vals.get('sequence') or self.sequence
                    vals.update(
                        {'sequence': self.sudo()._create_sequence({'sequence': sequence, 'abbreviation': seq, }).id})
        return super(ebsDocumentType, self).write(vals)

    @api.model
    def _create_sequence(self, vals):
        """ Create new no_gap entry sequence for every new Journal"""

        seq_name = vals['abbreviation']
        seq = {
            'name': 'Document Type ' + seq_name + 'Sequence',
            'implementation': 'no_gap',
            'prefix': seq_name.upper() + '/',
            'padding': 5,
            'number_increment': 1,
            'use_date_range': False,
        }
        if 'sequence' not in vals or not vals['sequence']:
            seq = self.env['ir.sequence'].create(seq)
            seq_date_range = seq._get_current_sequence()
            seq_date_range.number_next = vals.get(
                'sequence_number_next', 1)
            return seq
        else:
            sequence = vals['sequence']
            seq = sequence.write(seq)
            seq_date_range = sequence._get_current_sequence()
            seq_date_range.number_next = vals.get(
                'sequence_number_next', 1)
            return sequence


class ebsVisaType(models.Model):
    _name = 'ebs.visa.type'
    _description = 'Visa Type'

    name = fields.Char('Name')
