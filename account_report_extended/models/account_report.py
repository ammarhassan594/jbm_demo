from odoo import models, fields, api


class InheritAccountReport(models.AbstractModel):
    _inherit = 'account.report'



    @api.model
    def _query_get(self, options, domain=None):
        domain = self._get_options_domain(options) + (domain or [])
        domain.append(('move_id.closing_entry', '!=', True))
        self.env['account.move.line'].check_access_rights('read')

        query = self.env['account.move.line']._where_calc(domain)

        # Wrap the query with 'company_id IN (...)' to avoid bypassing company access rights.
        self.env['account.move.line']._apply_ir_rules(query)

        return query.get_sql()