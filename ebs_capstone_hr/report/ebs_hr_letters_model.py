from odoo import models, fields, api, _



class EbsHrLettersModel(models.TransientModel):
    _name = "ebs.hr.letters.model"
    _description = 'HR Letter Model'

    name = fields.Char(string='name')
    datas = fields.Binary(string='datas')