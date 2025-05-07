import base64

from odoo import http
from odoo.http import request


class ExcellenceBoard(http.Controller):
    @http.route("/GetExcellenceBoard/", auth="public", type="json", methods=["POST"])
    def get_excellence_board(self, **kwargs):
        data = []
        excellenceBoards = request.env['excellence.board'].sudo().search([])
        if excellenceBoards:
            for excellence in  excellenceBoards:
                data.append({
                    "id": excellence.id,
                    "name": excellence.name,
                    "code": excellence.code,
                    "issue_date": excellence.issue_date,
                    "attachment": True if excellence.attachment else False
                })
        return data

    @http.route("/GetExcellenceBoardAttachment/", auth="public", type="json", methods=["POST"])
    def get_excellence_board_attachment(self, **kwargs):
        data = []

        params = request.httprequest.args.to_dict()
        excellence_board_id = params.get("record_id")

        if excellence_board_id:
            ExcellenceBoards = request.env['excellence.board'].sudo().browse(int(excellence_board_id))
            if ExcellenceBoards:
                data.append({
                    "attachment": ExcellenceBoards.attachment if ExcellenceBoards.attachment else None
                })
        else:
            ExcellenceBoards = request.env['excellence.board'].sudo().search([])
            for record in ExcellenceBoards:
                data.append({
                    "id": record.id,
                    "attachment": record.attachment if record.attachment else None
                })

        return data
