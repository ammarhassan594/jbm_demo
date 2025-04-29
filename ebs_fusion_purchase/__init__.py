from . import models


from odoo import api, SUPERUSER_ID


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['base.automation'].sudo().create({
        'name': 'Late Delivery Reminder',
        'model_id': env.ref('purchase.model_purchase_order').id,
        'active': True,
        'trigger': 'on_time',
        'trg_date_id': env.ref('purchase.field_purchase_order__date_planned').id,
        'trg_date_range': 1,
        'trg_date_range_type': 'minutes',
        'state': 'next_activity',
        'activity_type_id': env.ref('mail.mail_activity_data_todo').id,
        'activity_summary': 'Follow up the receipt',
        'activity_user_type': 'generic',
    })
