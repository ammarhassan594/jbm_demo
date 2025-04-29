from odoo import models


class DmsDocuments(models.Model):
    _name = 'documents.document'
    _inherit = ['documents.document', 'dms.integration.mix']
