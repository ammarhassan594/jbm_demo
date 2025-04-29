# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

import logging
import pytz

from odoo import api, fields, models
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class MailActivityMixin(models.AbstractModel):
    _inherit = 'mail.activity.mixin'

    activity_ids = fields.One2many(groups="base.group_user,base_portal_user.group_user_portal")
    activity_type_id = fields.Many2one(groups="base.group_user,base_portal_user.group_user_portal")
    activity_summary = fields.Char(groups="base.group_user,base_portal_user.group_user_portal")
    activity_state = fields.Selection(groups="base.group_user,base_portal_user.group_user_portal")
