# -*- coding: utf-8 -*-
import ast
import json
from logging import getLogger
from odoo import _, SUPERUSER_ID
from odoo.http import Controller, request, route, Response, JsonRequest
from odoo.exceptions import AccessDenied, ValidationError, UserError

_logger = getLogger(__name__)


class MainApi(Controller):
    """
    There are URIs available:
    /api/<model>/<method>  POST     - Call method (with optional parameters)
    /api/<model>/<method>  GET     - Call method (with optional parameters)
    """

    @route(['/api/post/<string:model>/<string:method>'], auth='none',
           methods=["POST"], type='json', csrf=False)
    def post_record_method(self, model, method, id=None, **kwargs):
        """ POST method   """
        if not request.env['ir.model'].sudo().search([('model', '=', model)]):
            raise Exception('There is no model named %s' % model)

        record = request.env[model].sudo().search([('id', '=', id)])
        # if isinstance(data, str):
        #     data = ast.literal_eval(data)

        data = json.loads(request.httprequest.data.decode('utf-8'))
        # _logger.info('before data: %s , type: %s ' % (data, type(data)))
        # _logger.info('after data: %s , type: %s ' % (data, type(data)))
        if record:
            record = record.with_user(SUPERUSER_ID)
            method = getattr(record, method)
            return method(**data)
        return getattr(request.env[model].with_user(SUPERUSER_ID), method)(**data)

    @route('/api/get/<string:model>/<string:method>', auth='none', methods=["GET"], type='json', csrf=False)
    def model_method(self, model, method):
        """ GET method
               Response
                   http status
                   200 ok -> successful get data
                   401 Access Token may be expired or invalid
                   500 No model or method (Odoo Server error)
                   403 Unauthorized User -> id of user in access token not have permission
        """
        url_params = dict()
        if not request.env['ir.model'].sudo().search([('model', '=', model)]):
            raise Exception('There is no model named %s' % model)
        if request.httprequest.args:
            args = request.httprequest.args.to_dict()
            url_params.update(args)
        return getattr(request.env[model].with_user(SUPERUSER_ID), method)(**url_params)
