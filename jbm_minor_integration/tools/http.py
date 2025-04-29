# -*- coding: utf-8 -*-
from functools import wraps
import json
import ast
import odoo
from odoo import _
from odoo.http import JsonRequest, AuthenticationError, SessionExpiredException, serialize_exception, Response
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import AccessDenied, except_orm, AccessError
from odoo.tools import date_utils
from psycopg2 import IntegrityError
import werkzeug.datastructures
import werkzeug.exceptions
import werkzeug.local
import werkzeug.routing
import werkzeug.wrappers
import werkzeug.wsgi

import logging

_logger = logging.getLogger(__name__)


class CustomJsonRequest(JsonRequest):

    def __init__(self, *args):
        super(JsonRequest, self).__init__(*args)
        self.jsonp_handler = None
        self.params = {}
        args = self.httprequest.args
        jsonp = args.get('jsonp')
        self.jsonp = jsonp
        request = None
        request_id = args.get('id')
        api = self.httprequest.headers.get('Api-Access')
        if jsonp and self.httprequest.method == 'POST':
            # jsonp 2 steps step1 POST: save call
            def handler():
                self.session['jsonp_request_%s' % (request_id,)] = self.httprequest.form['r']
                self.session.modified = True
                headers = [('Content-Type', 'text/plain; charset=utf-8')]
                r = werkzeug.wrappers.Response(request_id, headers=headers)
                return r

            self.jsonp_handler = handler
            return
        elif jsonp and args.get('r'):
            # jsonp method GET
            request = args.get('r')
        elif jsonp and request_id:
            # jsonp 2 steps step2 GET: run and return result
            request = self.session.pop('jsonp_request_%s' % (request_id,), '{}')
        elif api and api == 'application/api' and self.httprequest.method == 'GET':
            request = json.dumps(args.to_dict())
        else:
            # regular jsonrpc2
            request = self.httprequest.get_data().decode(self.httprequest.charset)

        # Read POST content or POST Form Data named "request"
        try:
            self.jsonrequest = json.loads(request)
        except ValueError:
            msg = 'Invalid JSON data: %r' % (request,)
            _logger.info('%s: %s', self.httprequest.path, msg)
            raise werkzeug.exceptions.BadRequest(msg)
        # _logger.info('before jsonrequest: %s, type: %s ', self.jsonrequest, type(self.jsonrequest))
        if isinstance(self.jsonrequest, str):
            try:
                self.jsonrequest = ast.literal_eval(self.jsonrequest)
            except Exception as e:
                raise Exception('exception ', str(e))
            self.params = dict(self.jsonrequest.get("params", {}))
        else:
            self.params = dict(self.jsonrequest.get("params", {}))
        # _logger.info('after jsonrequest: %s, type: %s ', self.jsonrequest, type(self.jsonrequest))
        self.context = self.params.pop('context', dict(self.session.context))

    def _handle_exception(self, exception):
        """Called within an except block to allow converting exceptions
           to arbitrary responses. Anything returned (except None) will
           be used as response."""
        try:
            return super(JsonRequest, self)._handle_exception(exception)
        except Exception:
            if not isinstance(exception, SessionExpiredException):
                if exception.args and exception.args[0] == "bus.Bus not available in test mode":
                    _logger.info(exception)
                elif isinstance(exception, (odoo.exceptions.UserError,
                                            werkzeug.exceptions.NotFound)):
                    _logger.warning(exception)
                else:
                    _logger.exception("Exception during JSON request handling.")

            # determine request from me
            from_me = self.httprequest.headers.get('Api-Access') == 'application/api'
            if from_me:
                error = {
                    'http_status': 500,
                    'code': 500,
                    'message': "Odoo Server Error",
                    'data': serialize_exception(exception),
                }
            else:
                error = {
                    'code': 200,
                    'message': "Odoo Server Error",
                    'data': serialize_exception(exception),
                }
            # odoo base
            if isinstance(exception, werkzeug.exceptions.NotFound):
                error['http_status'] = 404
                error['code'] = 404
                error['message'] = "404: Not Found"
            if isinstance(exception, AuthenticationError):
                error['code'] = 100
                error['message'] = "Odoo Session Invalid"
            if isinstance(exception, SessionExpiredException):
                error['code'] = 100
                error['message'] = "Odoo Session Expired"
            # custom exception
            if from_me and isinstance(exception, (AccessDenied, AccessError)):
                error['http_status'] = 403
                error['code'] = 403
                error['message'] = "Access Denied"
            return self._json_response(error=error)

    def _json_response(self, result=None, error=None):
        http_status = 200
        from_me = self.httprequest.headers.get('Api-Access') == 'application/api'
        # _logger.info("Json From Me %s", from_me)
        response = {
            'jsonrpc': '2.0',
            'id': self.jsonrequest.get('id')
        }
        if error is not None:
            response['error'] = error
            if from_me and isinstance(error, dict):
                http_status = error.pop('http_status', 200)
        if result is not None:
            response['result'] = result
            if from_me and isinstance(result, dict):
                http_status = result.pop('http_status', 200)
        mime = 'application/json'
        body = json.dumps(response, default=date_utils.json_default)
        return Response(
            body, status=error and error.pop('http_status', http_status) or http_status,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )

JsonRequest.__init__ = CustomJsonRequest.__init__

JsonRequest._json_response = CustomJsonRequest._json_response

JsonRequest._handle_exception = CustomJsonRequest._handle_exception


class make_response():
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = decode_bytes(func(*args, **kwargs))
            return result

        return wrapper


def eval_request_params(kwargs):
    for k, v in kwargs.items():
        try:
            kwargs[k] = safe_eval(v)
        except Exception:
            continue


def decode_bytes(result):
    if isinstance(result, (list, tuple)):
        decoded_result = []
        for item in result:
            decoded_result.append(decode_bytes(item))
        return decoded_result
    if isinstance(result, dict):
        decoded_result = {}
        for k, v in result.items():
            decoded_result[decode_bytes(k)] = decode_bytes(v)
        return decoded_result
    if isinstance(result, bytes):
        return result.decode('utf-8')
    return result
