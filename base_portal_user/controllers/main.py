# -*- coding: utf-8 -*-

from odoo.addons.web.controllers.main import ensure_db
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.web import Home
from odoo.addons.portal.controllers.web import Home as portalHome
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
import logging
import werkzeug
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

_logger = logging.getLogger(__name__)


class Home(Home):

    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        if request.session.uid:
            current_user = request.env['res.users'].sudo().browse(request.session.uid)
            if not current_user.has_group('base.group_user') and current_user.has_group('base_portal_user.group_user_portal'):
                request.uid = request.session.uid
                try:
                    context = request.env['ir.http'].webclient_rendering_context()
                    response = request.render('web.webclient_bootstrap', qcontext=context)
                    response.headers['X-Frame-Options'] = 'DENY'
                    return response
                except AccessError:
                    return werkzeug.utils.redirect('/web/login?error=access')
        return super(Home, self).web_client(s_action, **kw)

class AuthSignupHomeInherit(AuthSignupHome):
#web login
    @http.route()
    def web_login(self, redirect=None, *args, **kw):
        ensure_db()
        response = super(AuthSignupHomeInherit, self).web_login(redirect=redirect, *args, **kw)
        if request.params['login_success']:
            current_user = request.env['res.users'].browse(request.uid)
            if current_user.has_group('base_portal_user.group_user_portal'):
                redirect = "/web"
                return request.redirect(redirect)
        return response

