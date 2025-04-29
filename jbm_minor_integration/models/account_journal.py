from logging import getLogger

from odoo import fields, models, api

_logger = getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def get_journals_api(self):
        try:
            journals = self.search([])
            journals_list = [{"Name": journal.name,
                              "Id": journal.id} for journal in journals]

            return {
                "Message": "Successfully get journals",
                "Journals": journals_list,
                "http_status": 200,
                "code": 200
            }

        except Exception as e:
            err = str(e)
            _logger.info("there is error {}".format(err))
            return {
                "Message": f"Error on get journals {err}",
                "http_status": 500,
                "code": 500
            }
