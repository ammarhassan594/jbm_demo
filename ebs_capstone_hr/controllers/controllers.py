# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, content_disposition
import os
import base64
from odoo.exceptions import AccessError


class HrController(http.Controller):

    def binary_content(self, id, env=None, field='datas', share_id=None, share_token=None,
                       download=False, filename=None, unique=False, filename_field='name'):


        record = request.env['ebs.hr.letters.model'].sudo().browse(int(id))


        status, content, filename, mimetype, filehash = request.env['ir.http']._binary_record_content(
            record, field=field, filename=None, filename_field=filename_field,
            default_mimetype='application/octet-stream')

        status, headers, content = request.env['ir.http']._binary_set_headers(
            status, content, filename, mimetype, unique, filehash=filehash, download=download)

        return status, headers, content

    def _get_file_response(self, id, field='datas', share_id=None, share_token=None):
        """
        returns the http response to download one file.

        """

        status, headers, content = self.binary_content(
            id, field=field, share_id=share_id, share_token=share_token, download=True)

        if status != 200:
            return request.env['ir.http']._response_by_status(status, headers, content)
        else:
            content_base64 = base64.b64decode(content)
            headers.append(('Content-Length', len(content_base64)))
            response = request.make_response(content_base64, headers)

        return response

    @http.route(['/documents/content/download/<int:id>'], type='http', auth='user')
    def documents_content(self, id):
        return self._get_file_response(id)
