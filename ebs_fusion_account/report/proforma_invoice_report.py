from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProformaInvoiceReport(models.AbstractModel):
    _name = 'report.ebs_fusion_account.report_proforma_invoice'
    _description = 'Proforma Invoice Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['account.payment'].browse(docids)
        not_proforma = docs.filtered(lambda s:s.is_proforma != True)
        if not_proforma:
            raise UserError('Payment is not proforma')
        return {
            'doc_ids': docs.ids,
            'doc_model': 'account.payment',
            'docs': docs,
        }
