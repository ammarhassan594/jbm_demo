from . import models
from . import wizard
from odoo import api, SUPERUSER_ID


def post_init(cr,registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['res.partner'].sudo().search([]).write({"is_customer": True})
    env.ref('contacts.res_partner_menu_contacts').sequence = 1
    env.ref('contacts.res_partner_menu_config').sequence = 3