from odoo import models, fields, api


class SmsTemplate(models.Model):

    _name = 'jbm.sms.template'

    subject = fields.Char()
    # employees_ids = fields.Many2many('hr.employee', string="Employees")
    employees = fields.Many2many('hr.employee')
    message = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in queue', 'In Queue'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    ], default='draft', Tracking=True)

    def send_fun(self):
        pass

    def cancel_state(self):
        self.state = 'cancelled'
