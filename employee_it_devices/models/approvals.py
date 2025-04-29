from odoo import models, fields, api, _


class InheritApprovals(models.Model):
    _inherit = 'approval.request'

    it_devices_id = fields.Many2many('it.devices')
    it_request_id = fields.Many2many('it.request')
    it_access_right_id = fields.Many2many('it.access.right.request')
    show_description = fields.Boolean(compute="_compute_show_description", default=False)
    it_description = fields.Text(string="Description")
    is_it_device = fields.Boolean(related="category_id.is_it_device")
    is_it_request = fields.Boolean(related="category_id.is_it_request")
    is_it_access_right = fields.Boolean(related="category_id.is_it_access_right")



    @api.depends('it_request_id', 'it_devices_id', 'it_access_right_id')
    def _compute_show_description(self):
        print('hello')
        if self.it_request_id:
            for req in self.it_request_id:
                if req.show_description:
                    self.show_description = True
                    break
                else:
                    self.show_description = False
        elif self.it_devices_id:
            for req in self.it_devices_id:
                if req.show_description:
                    self.show_description = True
                    break
                else:
                    self.show_description = False
        elif self.it_access_right_id:
            for req in self.it_access_right_id:
                if req.show_description:
                    self.show_description = True
                    break
                else:
                    self.show_description = False
        else:
            self.show_description = False
