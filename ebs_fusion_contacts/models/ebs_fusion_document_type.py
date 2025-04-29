from odoo import api, fields, models, _

TYPE_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')]


class ebsDocumentType(models.Model):
    _inherit = 'ebs.document.type'
    
    has_issue_expiry_date = fields.Selection(TYPE_SELECTION, string="Issue and Expiry Date", default="no", required=True)
    has_expiry_date = fields.Selection(TYPE_SELECTION, string="Expiry Date", default="no",required=True)
    has_issue_date = fields.Selection(TYPE_SELECTION, string="Issue Date", default="no", required=True)
    has_reminder_for_renewal = fields.Selection(TYPE_SELECTION, string="Reminder for Renewal", default="no", required=True)
    has_passport_serial_number = fields.Selection(TYPE_SELECTION, string="Passport Serial Number", default="no", required=True)
    has_qid_serial_number = fields.Selection(TYPE_SELECTION, string="QID Serial Number", default="no", required=True)
    has_po_box = fields.Selection(TYPE_SELECTION, string="P.O Box", default="no", required=True)
    has_email_address = fields.Selection(TYPE_SELECTION, string="Email Address", default="no", required=True)
    has_phone_number = fields.Selection(TYPE_SELECTION, string="Phone Number", default="no", required=True)
    has_reference_number = fields.Selection(TYPE_SELECTION, string="Reference Number", default="no", required=True)
    has_power_of_attorney_name = fields.Selection(TYPE_SELECTION, string="Power of attorney Name", default="no", required=True)
    has_tax_identification_no = fields.Selection(TYPE_SELECTION, string="Tax Identification No.", default="no", required=True)
    has_title_of_license = fields.Selection(TYPE_SELECTION, string="Title of License", default="no", required=True)
    has_membership_no = fields.Selection(TYPE_SELECTION, string="Membership No.", default="no", required=True)
    has_civil_defense_license = fields.Selection(TYPE_SELECTION, string="Civil Defense License", default="no", required=True)
    has_trade_license = fields.Selection(TYPE_SELECTION, string="Trade License", default="no", required=True)
    
    has_articles_of_association_notarization_date = fields.Selection(TYPE_SELECTION, string="Articles of Association Notarization Date", default="no", required=True)
    has_amendments_of_association_notarization_date = fields.Selection(TYPE_SELECTION, string="Amendments of Association Notarization Date", default="no", required=True)
    has_sspa_execution_date = fields.Selection(TYPE_SELECTION, string="Share Sale and Purchase Agreement Date", default="no", required=True)
    has_shareholders_agreement_date = fields.Selection(TYPE_SELECTION, string="Shareholders Agreement Date", default="no", required=True)
    has_service_agreement_date = fields.Selection(TYPE_SELECTION, string="Service Agreement Date", default="no", required=True)
    has_loan_agreement = fields.Selection(TYPE_SELECTION, string="Loan Agreement", default="no", required=True)
    has_other_agreement_date = fields.Selection(TYPE_SELECTION, string="Other Agreement Date", default="no", required=True)
    is_completed = fields.Selection(TYPE_SELECTION, string="Completed", default="no", required=True)
    is_legal = fields.Boolean("Legal")
    is_license = fields.Boolean("License")
    is_financial_audit = fields.Boolean('Financial Audit')

