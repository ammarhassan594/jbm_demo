# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment
from werkzeug.exceptions import NotFound


class WebsiteHrRecruitment(WebsiteHrRecruitment):

    @http.route('''/jobs/apply/<model("hr.job", "[('website_id', 'in', (False, current_website_id))]"):job>''',
                type='http', auth="public", website=True)
    def jobs_apply(self, job, **kwargs):
        if not job.can_access_from_current_website():
            raise NotFound()

        error = {}
        default = {}
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')
        countries = request.env['res.country'].sudo().search([])
        return request.render("website_hr_recruitment.apply", {
            'job': job,
            'countries': countries,
            'error': error,
            'default': default,
        })
