# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EmergencyContact(models.Model):
    _name = 'emergency.contact'

    name = fields.Char(
        string='Contact Name'
    )

    phone = fields.Char(
        string='Contact Phone'
    )

    emergency_contact_relation = fields.Char(
        string='Emergency Contact Relation'
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee'
    )
