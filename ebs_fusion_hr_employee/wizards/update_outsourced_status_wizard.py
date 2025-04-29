from odoo import fields, models, api, _


class UpdateOutsourcedStatusWizard(models.TransientModel):
    _name = 'update.outsourced.status.wizard'
    _description = 'Update Outsourced Status Wizard'

    outsourced_status = fields.Selection([
        ('visa_ready_to_use', 'Visa Ready To Use'),
        ('inside_country', 'Inside The Country'),
        ('inside_country_mev', 'Inside the Country – MEV'),
        ('onboarding', 'Outside Visa Test Process'),
        ('potential_candidate', 'Potential Candidate'),
        ('sponsored_outside_country', 'Sponsored – Outside The Country'),
        ('sponsored_absconding', 'Sponsored – Absconding'),
        ('sponsored', 'Sponsored'),
        ('sponsored_transfer_rejected', 'Sponsored – Transfer Rejected'),
        ('sponsored_Transferring_out', 'Sponsored – Transferring Out'),
        ('work_multi_entry', 'Work - Multi Entry'),
        ('sponsored_to_cancelled', 'Sponsored – To be Cancelled'),
        ('sponsored_outside_country_to_cancelled', 'Sponsored - Outside the Country - To be Cancelled'),
        ('transferring_in', 'Transferring In'),
        ('transferred_out', 'Transferred Out'),
        ('work_permit', 'Work Permit'),
        ('cancelled', 'Cancelled'),
    ], string='Status')
    employee_ids = fields.Many2many(comodel_name='hr.employee')

    def button_confirm(self):
        for employee in self.employee_ids:
            employee.write({'outsourced_status': self.outsourced_status})

