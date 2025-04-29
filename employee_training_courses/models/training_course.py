from odoo import models, fields, api, _


class TrainingCourse(models.Model):
    _name = "training.course"

    name = fields.Char(string="Course Name")
    code = fields.Char(string="Code")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    location = fields.Char(string="Location")
    remarks = fields.Text(string="Remarks")
    category_id = fields.Many2one('product.category', string="Product Category")
    product_id = fields.Many2one('product.product', string="Product")
