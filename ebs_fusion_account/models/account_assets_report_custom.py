from odoo import models, fields, api

class AccountAssetsReportCustom(models.AbstractModel):
    _inherit = 'account.assets.report'

    def _get_assets_lines(self, options):
        "Get the data from the database"
        where_account_move = ""
        if options.get('all_entries') is False:
            where_account_move += " AND state = 'posted'"

        sql = """
                SELECT asset.id as asset_id,
                       asset.parent_id as parent_id,
                       asset.name as asset_name,
                       asset.value_residual as asset_value,
                       asset.original_value as asset_original_value,
                       asset.first_depreciation_date as asset_date,
                       max_date_before.date as max_date_before,
                       asset.disposal_date as asset_disposal_date,
                       asset.acquisition_date as asset_acquisition_date,
                       asset.method as asset_method,
                       (SELECT COUNT(*) FROM account_move WHERE asset_id = asset.id AND asset_value_change != 't') as asset_method_number,
                       asset.method_period as asset_method_period,
                       asset.method_progress_factor as asset_method_progress_factor,
                       asset.state as asset_state,
                       account.code as account_code,
                       account.name as account_name,
                       account.id as account_id,
                       COALESCE(first_move.asset_depreciated_value, move_before.asset_depreciated_value, 0.0) as depreciated_start,
                       COALESCE(first_move.asset_remaining_value, move_before.asset_remaining_value, 0.0) as remaining_start,
                       COALESCE(last_move.asset_depreciated_value, move_before.asset_depreciated_value, 0.0) as depreciated_end,
                       COALESCE(last_move.asset_remaining_value, move_before.asset_remaining_value, 0.0) as remaining_end,
                       COALESCE(first_move.amount_total, 0.0) as depreciation
                FROM account_asset as asset
                LEFT JOIN account_account as account ON asset.account_asset_id = account.id
                LEFT OUTER JOIN (SELECT MIN(date) as date, asset_id FROM account_move WHERE date >= %(date_from)s AND date <= %(date_to)s {where_account_move} GROUP BY asset_id) min_date_in ON min_date_in.asset_id = asset.id
                LEFT OUTER JOIN (SELECT MAX(date) as date, asset_id FROM account_move WHERE date >= %(date_from)s AND date <= %(date_to)s {where_account_move} GROUP BY asset_id) max_date_in ON max_date_in.asset_id = asset.id
                LEFT OUTER JOIN (SELECT MAX(date) as date, asset_id FROM account_move WHERE date <= %(date_from)s GROUP BY asset_id) max_date_before ON max_date_before.asset_id = asset.id
                LEFT OUTER JOIN account_move as first_move ON first_move.id = (SELECT m.id FROM account_move m WHERE m.asset_id = asset.id AND m.date = min_date_in.date ORDER BY m.id ASC LIMIT 1)
                LEFT OUTER JOIN account_move as last_move ON last_move.id = (SELECT m.id FROM account_move m WHERE m.asset_id = asset.id AND m.date = max_date_in.date ORDER BY m.id DESC LIMIT 1)
                LEFT OUTER JOIN account_move as move_before ON move_before.id = (SELECT m.id FROM account_move m WHERE m.asset_id = asset.id AND m.date = max_date_before.date ORDER BY m.id DESC LIMIT 1)
                WHERE asset.company_id in %(company_ids)s
                AND asset.acquisition_date <= %(date_to)s
                AND (asset.disposal_date >= %(date_from)s OR asset.disposal_date IS NULL)
                AND asset.state not in ('model', 'draft')
                AND asset.asset_type = 'purchase'

                ORDER BY account.code;
            """.format(where_account_move=where_account_move)

        date_to = options['date']['date_to']
        date_from = options['date']['date_from']
        company_ids = tuple(t['id'] for t in self._get_options_companies(options))
        print(self._context,"LLLLLLLLLLLLcontext")
        if 'assetbutton' in self._context:
            partner_id = self.env['res.partner'].search([('id','=',self._context.get('active_id'))])
            company_id = self.env['res.company'].search([('name','=',partner_id.name)])
            company_ids = tuple(t.id for t in company_id)
        print(company_ids,"@@@@@@@companies")
        self.flush()
        self.env.cr.execute(sql, {'date_to': date_to, 'date_from': date_from, 'company_ids': company_ids})
        results = self.env.cr.dictfetchall()
        return results