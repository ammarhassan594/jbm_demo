from odoo import models, fields, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    role_distribution = fields.Many2one(comodel_name="role.distribution", copy=False)

    @api.model
    def create(self, vals):
        # Creates a role distribution and assign to the field
        project = super(ProjectProject, self).create(vals)
        role_distribution = self.env['role.distribution'].create({'name': project.name})
        project.role_distribution = role_distribution.id
        return project
