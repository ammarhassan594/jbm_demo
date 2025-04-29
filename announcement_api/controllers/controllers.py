# -*- coding: utf-8 -*-
import base64
from odoo import http
from odoo.http import request


class AnnouncementApi(http.Controller):
    @http.route("/GetAnnouncement/", auth="public", type="json", methods=["POST"])
    def get_announcement(self, **kw):
        data = []
        announcements = request.env['announcement'].sudo().search([])
        if announcements:
            for announcement in announcements:
                data.append({
                    "id": announcement.id,
                    "name": announcement.name,
                    "date": announcement.date.strftime("%d/%m/%Y %H:%M:%S") if announcement.date else '',
                    "has_attachment": announcement.attachment and True or False
                    # "attachment": list(base64.standard_b64decode(announcement.attachment))
                    # "attachment": base64.encodebytes(announcement.attachment)
                })
            # announcements = announcements.read(['name', 'date', 'attachment'])
        return data

    @http.route("/GetAnnouncementAttachment/", auth="public", type="json", methods=["POST"])
    def get_announcement_attachment(self, **kw):
        data = []

        params = request.httprequest.args.to_dict()
        announcement_id = params.get("record_id")

        if announcement_id:
            announcement = request.env['announcement'].sudo().browse(int(announcement_id))
            if announcement:
                data.append({
                    "attachment": announcement.attachment if announcement.attachment else None
                })
        else:
            announcements = request.env['announcement'].sudo().search([])
            for announcement in announcements:
                data.append({
                    "id": announcement.id,
                    "attachment": announcement.attachment if announcement.attachment else None
                })

        return data
