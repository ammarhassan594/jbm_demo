from logging import getLogger

from odoo import fields, models, api

_logger = getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # @api.model
    # def get_partner_api(self):
    #     try:
    #         partners = self.search([])
    #         partner_list = [{"Name": partner.name,
    #                          "Id": partner.id} for partner in partners]
    #
    #         return {
    #             "Message": "Successfully get partners",
    #             "Partners": partner_list,
    #             "code": 200
    #         }
    #
    #     except Exception as e:
    #         err = str(e)
    #         _logger.info("there is error {}".format(err))
    #         return {
    #             "Message": f"Error on get partners {err}",
    #             "http_status": 500,
    #             "code": 500
    #         }
