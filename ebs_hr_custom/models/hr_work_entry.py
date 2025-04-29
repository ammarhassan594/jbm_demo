from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, safe_eval


class ResourceCalender(models.Model):
    _inherit = 'resource.calendar'

    default_work_calendar = fields.Selection([
        ('staff', 'Staff'),
        ('in_house', 'In house'),
        ('temp', 'Temporary'),
    ], string='Default Work Calendar')

    def get_working_days(self, start_date, end_date):
        self.ensure_one()
        if start_date and end_date:
            # check for type
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, DF).date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, DF).date()
            # get list of all days
            all_days = (start_date + timedelta(day) for day in range((end_date - start_date).days + 1))
            # filter business days
            # weekday from 0 to 4. 0 is monday adn 4 is friday
            # increase counter in each iteration if it is a weekday
            workdays = list(set(self.attendance_ids.mapped('dayofweek')))
            workdays = [int(w) for w in workdays]
            # count = sum(1 for day in all_days if day.weekday() in [0, 1, 2, 3, 6])
            count = sum(1 for day in all_days if day.weekday() in workdays)
            return count
        else:
            return 0.0

    # @api.constrains('default_work_calendar')
    # def _check_default_work_calendar(self):
    #     for rec in self:
    #         has_default = self.sudo().search([('default_work_calendar', '=', rec.default_work_calendar), ('id', '!=', rec.id)])
    #         if has_default:
    #             raise ValidationError(_("Default work calendar already set."))


class WorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    main_project = fields.Many2one(related="employee_id.main_project",
                                   string='Work Location', store=True)
