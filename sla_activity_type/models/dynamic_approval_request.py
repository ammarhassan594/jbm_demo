import pytz
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields


class InheritDynamicApprovalRequest(models.Model):
    _inherit = 'dynamic.approval.request'

    def get_activity_type_request(self):
        """Return activity type of request to create an active with value of activity type
            Every request related to level so get value of activity type field on level
        """
        self.ensure_one()
        return self.dynamic_approve_level_id.activity_type_id
