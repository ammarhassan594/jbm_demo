from odoo import models, fields


class ExcellenceElement(models.Model):
    _name = 'excellence.element'
    _rec_name = 'employee_id'

    type_id = fields.Many2one('excellence.element.type')
    date_taken = fields.Date("Date")
    attachment_ids = fields.Many2many('ir.attachment', string="Attachment")
    remarks = fields.Text()
    employee_id = fields.Many2one('hr.employee', string="Employee")

