from odoo import api, fields, models, _


class DocumentsFolderCustom(models.Model):
    _inherit = 'documents.folder'
    is_default_folder = fields.Boolean(
        string='Is Default Folder',
        required=False
    )
    level = fields.Integer('Level', compute='compute_level')

    def compute_level(self):
        for rec in self:
            rec.level = rec.calculate_level()


    def calculate_level(self):
        for rec in self:
            if not rec.parent_folder_id:
                rec.level = 0
            else:
                rec.level = rec.parent_folder_id.calculate_level() + 1
        return rec.level


