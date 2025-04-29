import logging
import datetime

from odoo import models, fields, api, _

from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class AllowanceTypeConditions(models.Model):
    _name = 'allowance.type.conditions'

    @api.model
    def _default_python_code(self):
        return """ # Available variables:
                        # datetime: object
                        # dateutil: object
                        # time: object
                        # context_today
                        # user: current user when run condition.
                        # record: object containing the record as sales order.
                        # result = True or False\n\n\n\n
                    """

    model_id = fields.Many2one('ir.model', string="Model")
    model = fields.Char(related='model_id.model', store=True)

    condition_type = fields.Selection(
        selection=[('domain', 'Domain'),
                   ('field_selection', 'Field Selection'),
                   ('python_code', 'Python Code'),
                   ],
        default='field_selection')

    allowance_type_id = fields.Many2one('allowance.type', string="Allowance Type")

    filter_domain = fields.Char(string='Domain')

    field_name = fields.Char()

    python_code = fields.Text(
        default=_default_python_code,
    )

    operator = fields.Selection(
        selection=[
            ('==', '='),
            ('<=', '<='),
            ('<', '<'),
            ('>=', '>='),
            ('>', '>'),
        ],
        default='<=',
    )
    value_type = fields.Selection(
        selection=[
            ('fixed', 'Fixed Value'),
            ('dynamic', 'Dynamic'),
        ],
        string='Type',
        default='dynamic',
    )

    value = fields.Char(
        string='Value',
        help='if type is dynamic: ex. partner_id.credit_limit. if type is fixed: ex. 10',
    )

    @api.onchange('condition_type', 'model_id')
    def onchange_condition_type(self):
        """ reset all fields when user change type """
        for record in self:
            record.value_type = False
            record.field_name = False
            record.value = False
            record.filter_domain = False
            record.python_code = False

    @api.onchange('value_type')
    def onchange_value_type(self):
        """ reset value """
        for record in self:
            record.value = False

    def _is_condition_matched_field_selection(self, res):
        """ return true / false based on calculation type """
        self.ensure_one()
        value_compare = self.value
        eval_dict = {'record': res}
        try:
            field_name_value = safe_eval('record.' + str(self.field_name), eval_dict)
            if self.value_type == 'dynamic':
                value_compare = safe_eval('record.' + str(value_compare), eval_dict)
            test = safe_eval(str(field_name_value) + self.operator + str(value_compare))
        except Exception as e:
            _logger.warning(e)
            test = False
        return test

    def _is_condition_matched_domain(self, res):
        """ return true / false based on calculation type """
        print('res res:::', res)

        self.ensure_one()
        evaluation_context = {
            # 'datetime': safe_eval.datetime,
            'context_today': datetime.datetime.now,
        }
        try:
            domain = safe_eval(self.filter_domain or '[]', evaluation_context)
            domain.extend([('id', 'in', res.ids)])
            data = self.env[self.model].sudo().search(domain)
            print('data::::', data)
            test = True if data else False
        except Exception as e:
            _logger.warning(e)
            test = False
        return test

    def _is_condition_matched_python_code(self, res):
        """ return true / false based on calculation type """
        self.ensure_one()
        try:
            localdict = {
                # 'datetime': safe_eval.datetime,
                # 'dateutil': safe_eval.dateutil,
                'time': safe_eval.time,
                'context_today': datetime.datetime.now,
                'user': self.env.user,
                'record': res,
            }
            safe_eval(self.python_code, localdict, mode="exec", nocopy=True)
            test = localdict['result']
        except Exception as e:
            _logger.warning(e)
            test = False
        return test

    def is_condition_matched(self, res):
        """ check if condition is matched with record """
        self.ensure_one()
        if self.condition_type == 'field_selection':
            return self._is_condition_matched_field_selection(res)
        elif self.condition_type == 'domain':
            return self._is_condition_matched_domain(res)
        elif self.condition_type == 'python_code':
            return self._is_condition_matched_python_code(res)
