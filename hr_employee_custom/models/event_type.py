from odoo import fields, models, api


class EventType(models.Model):
    _name = 'sap.event.type'
    _description = 'SAP Event Type'

    name = fields.Char(string="Code", required=True)
    description = fields.Char(
        string='Description',
        required=False)
    event_type_reason_ids = fields.One2many(
        comodel_name='sap.event.type.reason',
        inverse_name='event_type_id',
        string='Reasons',
        required=False)
    is_new_hire = fields.Boolean(
        string='Is New Hire',
        required=False, default=False)
    is_probation = fields.Boolean(
        string='Is Probation',
        required=False, default=False)

    def name_get(self):
        names = []
        for record in self:
            names.append((record.id, "%s - %s" % (record.name, record.description)))
        return names


class EventTypeReason(models.Model):
    _name = 'sap.event.type.reason'
    _description = 'SAP Event Type Reason'

    name = fields.Char(string="Code", required=True)
    description = fields.Char(
        string='Description',
        required=False)
    event_type_id = fields.Many2one(
        comodel_name='sap.event.type',
        string='Event Type',
        required=True, ondelete='cascade')

    def name_get(self):
        names = []
        for record in self:
            names.append((record.id, "%s - %s" % (record.name, record.description)))
        return names
