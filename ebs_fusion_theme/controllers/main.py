import base64
from io import BytesIO
import json
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.website.controllers.form import WebsiteForm
from psycopg2 import IntegrityError
from datetime import date, datetime
from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.exceptions import ValidationError
from odoo.osv.expression import OR
from dateutil.parser import parse
from odoo import http
from odoo.addons.web.controllers.main import Home
from odoo.http import request
from werkzeug.exceptions import BadRequest
from odoo.exceptions import ValidationError, UserError

class FusionWebsiteForm(WebsiteForm):

    @http.route('/website/form', type='http', auth="public", methods=['POST'], multilang=False)
    def website_form_empty(self, **kwargs):
        # This is a workaround to don't add language prefix to <form action="/website/form/" ...>
        return ""

    @http.route('/website/form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def website_form(self, model_name, **kwargs):
        # Partial CSRF check, only performed when session is authenticated, as there
        # is no real risk for unauthenticated sessions here. It's a common case for
        # embedded forms now: SameSite policy rejects the cookies, so the session
        # is lost, and the CSRF check fails, breaking the post for no good reason.
        csrf_token = request.params.pop('csrf_token', None)
        if request.session.uid and not request.validate_csrf(csrf_token):
            raise BadRequest('Session expired (invalid CSRF token)')

        try:
            # The except clause below should not let what has been done inside
            # here be committed. It should not either roll back everything in
            # this controller method. Instead, we use a savepoint to roll back
            # what has been done inside the try clause.
            with request.env.cr.savepoint():
                if request.env['ir.http']._verify_request_recaptcha_token('website_form'):
                    return self._handle_website_form(model_name, **kwargs)
            error = _("Suspicious activity detected by Google reCaptcha.")
        except (ValidationError, UserError) as e:
            error = e.args[0]
        return json.dumps({
            'error': error,
        })

    def _handle_website_form(self, model_name, **kwargs):
        model_record = request.env['ir.model'].sudo().search([('model', '=', model_name), ('website_form_access', '=', True)])
        if not model_record:
            return json.dumps({
                'error': _("The form's specified model does not exist")
            })

        try:
            data = self.extract_data(model_record, request.params)
        # If we encounter an issue while extracting data
        except ValidationError as e:
            # I couldn't find a cleaner way to pass data to an exception
            return json.dumps({'error_fields' : e.args[0]})

        try:
            id_record = self.insert_record(request, model_record, data['record'], data['custom'], data.get('meta'))
            if id_record:
                self.insert_attachment(model_record, id_record, data['attachments'])
                # in case of an email, we want to send it immediately instead of waiting
                # for the email queue to process
                if model_name == 'mail.mail':
                    request.env[model_name].sudo().browse(id_record).send()

        # Some fields have additional SQL constraints that we can't check generically
        # Ex: crm.lead.probability which is a float between 0 and 1
        # TODO: How to get the name of the erroneous field ?
        except IntegrityError:
            return json.dumps(False)

        request.session['form_builder_model_model'] = model_record.model
        request.session['form_builder_model'] = model_record.name
        request.session['form_builder_id'] = id_record
        if model_name == 'crm.lead' and 'service_type' in kwargs:
            service = kwargs.get('service_type')
            lead_id = request.env['crm.lead'].browse([id_record])
            if service == 'company':
                company_id = request.env['res.company'].sudo().search([('name', '=', 'Fusion Middle East UAE')],
                                                                      limit=1)
                lead_id.sudo().write({'company_id': company_id.id})
            if service == 'PRO':
                company_id = request.env['res.company'].sudo().search([('name', '=', 'Fusion Support Services')],
                                                                      limit=1)
                lead_id.sudo().write({'company_id': company_id.id})
            if service == 'outsourcing':
                company_id = request.env['res.company'].sudo().search([('name', '=', 'Fusion Outsourcing & Services')],
                                                                      limit=1)
                lead_id.sudo().write({'company_id': company_id.id})
            if service == 'project':
                company_id = request.env['res.company'].sudo().search([('name', '=', 'Fusion Technology')], limit=1)
                lead_id.sudo().write({'company_id': company_id.id})
            if service == 'general':
                company_id = request.env['res.company'].sudo().search([('name', '=', 'Fusion Global Services')],
                                                                      limit=1)
                lead_id.sudo().write({'company_id': company_id.id})
        return json.dumps({'id': id_record})



class CustomerPortal(CustomerPortal):

    @http.route(['/payments'], type='http', auth="public", website=True)
    def portal_payments_menu(self, **kw):
        values = {
            'page_name': 'proforma_invoices',
            'main_proforma_menu': True
        }
        return request.render("ebs_fusion_theme.portal_payments_menu", values)

    @http.route(['/my/payments', '/my/payments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_payments(self, page=1, date_begin=None, date_end=None, sortby=None, search=None,
                           search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        Payments = request.env['account.payment']

        domain = [('partner_id', '=', partner.last_client_id.id)]

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date desc'},
            'amount': {'label': _('Amount'), 'order': 'amount desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('State'), 'order': 'state'},
        }

        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Name'), 'type': 'text'},
            'date': {'input': 'date', 'label': _('Date'), 'type': 'date'},
            'status': {'input': 'status', 'label': _('Status'), 'type': 'text'},
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>'),
                        'type': 'text'},
        }
        parent_menu_name = ''
        if kw.get('is_proforma'):
            domain.append(('is_proforma', '=', True))
            domain.append(('payment_sequence', '!=', False))
            is_proforma = True
            if kw.get('state'):
                domain.append(('state', '=', kw.get('state')))
                if kw.get('state') == 'draft':
                    parent_menu_name = 'New Proforma Invoices'
                if kw.get('state') == 'posted':
                    parent_menu_name = 'Paid Proforma Invoices'
            searchbar_inputs.update({'sequence': {'input': 'payment_sequence', 'label': _('Sequence'), 'type': 'text'}})
        else:
            domain.append(('is_proforma', '=', False))
            domain.append(('state', '=', 'posted'))
            is_proforma = False

        total_pi = request.env['account.payment'].sudo().search([
            ('partner_id', '=', partner.last_client_id.id),
            ('is_proforma', '=', True),
            ('payment_sequence', '!=', False),
        ])
        total_pi_not_paid_amount = sum(total_pi.filtered(lambda o: o.state == 'draft').mapped('amount'))
        total_pi_paid_amount = sum(total_pi.filtered(lambda o: o.state == 'posted').mapped('amount'))
        total_invoice = request.env['account.move'].sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('partner_id', '=', partner.last_client_id.id),
            ('state', '=', 'posted'),
        ])
        total_invoice_not_paid_amount = sum(
            total_invoice.filtered(lambda o: o.payment_state != 'paid').mapped('amount_total'))
        total_invoice_paid_amount = sum(
            total_invoice.filtered(lambda o: o.payment_state == 'paid').mapped('amount_total'))

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        if search and search_in:
            search_domain = []
            if search_in == 'name':
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in == 'payment_sequence':
                search_domain = OR([search_domain, [('payment_sequence', 'ilike', search)]])
            if search_in == 'date':
                search_domain = OR([search_domain, [('date', 'ilike', search)]])
            if search_in == 'status':
                search_domain = OR([search_domain, [('state', 'ilike', search)]])
            if search_in == 'content':
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('state', 'ilike', search)]])
            domain += search_domain

        # count for pager
        payment_count = Payments.sudo().search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/payments",
            url_args={'is_proforma': kw.get('is_proforma'), 'state': kw.get('state')},
            total=payment_count,
            page=page,
            step=10
        )
        # search the count to display, according to the pager data
        payments = Payments.sudo().search(domain, order=sort_order, limit=10, offset=pager['offset'])
        request.session['payments_history'] = payments.ids[:100]
        employee_ids = request.env['hr.employee'].sudo().search([])
        all_services = request.env['ebs.crm.service'].sudo().search([], order='category_id')
        nationalities = request.env['res.country'].sudo().search([])
        job_positions = request.env['hr.job'].sudo().search([])
        related_clients = request.env['ebs.client.contact'].sudo().search([('partner_id', '=', partner.id)]).mapped(
            'client_id')
        client_contracts = request.env['ebs.crm.proposal'].sudo().search(
            [('contact_id', '=', partner.last_client_id.id), ('type', '=', 'proposal'), ('state', '=', 'active')])
        client_employee_ids = request.env['hr.employee'].sudo().search(
            [('partner_parent_id', '=', partner.last_client_id.id)])

        values.update({
            'date': date_begin,
            'payments': payments.sudo(),
            'total_pi_not_paid_amount': total_pi_not_paid_amount,
            'total_pi_paid_amount': total_pi_paid_amount,
            'total_invoice_not_paid_amount': total_invoice_not_paid_amount,
            'total_invoice_paid_amount': total_invoice_paid_amount,
            'page_name': 'payment',
            'pager': pager,
            'default_url': '/my/payments',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search': search,
            'search_in': search_in,
            'employee_ids': employee_ids,
            'all_services': all_services,
            'client_employee_ids': client_employee_ids,
            'nationalities': nationalities,
            'job_positions': job_positions,
            'related_clients': related_clients,
            'last_client_id': partner.last_client_id.id,
            'client_contracts': client_contracts,
            'is_proforma': is_proforma,
            'parent_menu_name': parent_menu_name,
        })
        return request.render("ebs_fusion_theme.portal_my_payments", values)

    @http.route(['/my/payments/<int:payment_id>'], type='http', auth="public", website=True)
    def portal_payment_page(self, payment_id, report_type=None, access_token=None, message=False, download=False, **kw):
        partner = request.env.user.partner_id
        payment_sudo = request.env['account.payment'].sudo().browse(payment_id)
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=payment_sudo, report_type=report_type,
                                     report_ref='ebs_fusion_account.action_proforma_invoice_report',
                                     download=download)
        employee_ids = request.env['hr.employee'].sudo().search([])
        all_services = request.env['ebs.crm.service'].sudo().search([], order='category_id')
        nationalities = request.env['res.country'].sudo().search([])
        job_positions = request.env['hr.job'].sudo().search([])
        partner_id = request.env.user.partner_id
        client_id = partner_id.last_client_id
        related_clients = request.env['ebs.client.contact'].sudo().search([('partner_id', '=', partner.id)]).mapped(
            'client_id')
        client_contracts = request.env['ebs.crm.proposal'].sudo().search(
            [('contact_id', '=', client_id.id), ('type', '=', 'proposal'), ('state', '=', 'active')])
        client_employee_ids = request.env['hr.employee'].sudo().search(
            [('partner_parent_id', '=', client_id.id)])
        parent_menu_name = ''
        parent_menu_url = ''
        if payment_sudo.is_proforma:
            parent_menu_url = '/my/payments?is_proforma=true&state=%s' % payment_sudo.state
            if payment_sudo.state == 'draft':
                parent_menu_name = 'New Proforma Invoices'
            if payment_sudo.state == 'posted':
                parent_menu_name = 'Paid Proforma Invoices'
        values = {
            'payment_sudo': payment_sudo,
            'employee_ids': employee_ids,
            'all_services': all_services,
            'client_employee_ids': client_employee_ids,
            'nationalities': nationalities,
            'job_positions': job_positions,
            'related_clients': related_clients,
            'client_contracts': client_contracts,
            'last_client_id': partner.last_client_id.id,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': payment_sudo.partner_id.id,
            'report_type': 'html',
            'is_proforma': payment_sudo.is_proforma,
            'parent_menu_name': parent_menu_name,
            'parent_menu_url': parent_menu_url,
            'download_url': '/my/payments/%s?report_type=pdf&download=True' % payment_id,
            'report_html_url': '/my/payments/%s?report_type=html' % payment_id,
            'action': request.env.ref('account.action_account_payments'),
        }

        return request.render('ebs_fusion_theme.payment_portal_template', values)

    def contract_create_update_vals_qid_radio_yes(self, kw, contract):
        return {
            'name': kw.get('%s-contract_full_name' % (contract.id)).upper(),
            'arabic_name': kw.get('%s-contract_name_ar' % (contract.id)),
            'mobile': kw.get('%s-contract_phone' % (contract.id)),
            'qid_ref_no': kw.get('%s-contract_qid' % (contract.id)),
            'qid_occupation': kw.get('%s-contract_job_position' % (contract.id)),
            'qid_expiry_date': parse(kw.get('%s-contract_qid_expiry_date' % (contract.id))) if kw.get(
                '%s-contract_qid_expiry_date' % (contract.id)) else None,
            'qid_residency_type': kw.get('%s-contract_residency_type' % (contract.id)),
            'qid_birth_date': parse(kw.get('%s-contract_qid_birth_date' % (contract.id))) if kw.get(
                '%s-contract_qid_birth_date' % (contract.id)) else None,
            'qid_resident': True
        }

    def contract_create_update_vals_qid_radio_no(self, kw, contract):
        return {
            'name': kw.get('%s-contract_full_name' % (contract.id)).upper(),
            'arabic_name': kw.get('%s-contract_name_ar' % (contract.id)),
            'mobile': kw.get('%s-contract_phone' % (contract.id)),
            'ps_passport_ref_no': kw.get('%s-contract_passport' % (contract.id)),
            'ps_first_name': kw.get('%s-contract_passport_name' % (contract.id)),
            'ps_expiry_date': parse(kw.get('%s-contract_expiry_date' % (contract.id))) if kw.get(
                '%s-contract_expiry_date' % (contract.id)) else None,
            'ps_passport_type': kw.get('%s-contract_passport_type' % (contract.id)),
            'ps_country_passport_id': kw.get('%s-contract_nationality' % (contract.id)),
            'ps_birth_date': parse(kw.get('%s-contract_birth_date' % (contract.id))) if kw.get(
                '%s-contract_birth_date' % (contract.id)) else None,
            'ps_gender': kw.get('%s-contract_gender' % (contract.id)),
            'qid_resident': False
        }

    def commercial_license_vals_create_update_qid_radio_no(self, kw, client_id):
        return {
            'name': kw.get('manager_in_charge_name').upper() or False,
            'mobile': kw.get('manager_in_charge_phone') or False,
            'email': kw.get('manager_in_charge_email') or False,
            'last_client_id': client_id.id,
            'permission': kw.get('manager_in_charge_permission') or False,
            'arabic_name': kw.get('manager_in_charge_name_ar') or False,
            'is_manager_cl': True,
            'ps_passport_ref_no': kw.get('manager_in_charge_passport') or False,
            'ps_first_name': kw.get('manager_in_charge_passport_name').upper() or False,
            'ps_expiry_date': parse(kw.get('expiry_date_extra_contact')) if kw.get(
                'expiry_date_extra_contact') else None,
            'ps_passport_type': kw.get('manager_in_charge_passport_type') or False,
            'ps_country_passport_id': int(kw.get('manager_in_charge_nationality')) if kw.get(
                'manager_in_charge_nationality') else False,
            'ps_birth_date': parse(kw.get('manager_in_charge_birth_date')) if kw[
                'manager_in_charge_birth_date'] else None,
            'gender': kw.get('manager_in_charge_gender') or False,
            'qid_resident': False if kw.get('manager_qid_radio') == 'no' else True,
        }

    def commercial_license_vals_create_update_qid_radio_yes(self, kw, client_id):
        return {
            'name': kw.get('manager_in_charge_name').upper() or False,
            'mobile': kw.get('manager_in_charge_phone') or False,
            'email': kw.get('manager_in_charge_email') or False,
            'last_client_id': client_id.id,
            'permission': kw.get('manager_in_charge_permission') or False,
            'arabic_name': kw.get('manager_in_charge_name_ar') or False,
            'is_manager_cl': True,
            'qid_occupation': int(kw.get('manager_in_charge_job_position')) if kw.get(
                'manager_in_charge_job_position') else False,
            'qid_birth_date': parse(kw.get('manager_in_charge_qid_birth_date')) if kw.get(
                'manager_in_charge_qid_birth_date') else None,
            'qid_expiry_date': parse(kw.get('manager_in_charge_qid_expiry_date')) if kw.get(
                'manager_in_charge_qid_expiry_date') else False,
            'qid_ref_no': kw.get('manager_in_charge_qid') or False,
            'qid_residency_type': kw.get('manager_in_charge_residency_type') or False,
            'qid_resident': True if kw.get('manager_qid_radio') == 'yes' else False,
        }

    def create_passport_qid_document(self, contact, file):
        return request.env['ir.attachment'].sudo().create({
            'name': file.filename,
            'type': 'binary',
            'datas': base64.b64encode(file.read()),
            'res_model': contact._name,
            'public': True,
            'res_id': contact.id
        })

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Employees = request.env['hr.employee']
        Payments = request.env['account.payment']
        employee_count = Employees.sudo().search_count([
            ('employee_type', '=', 'client_employee'),
            ('partner_parent_id', '=', partner.id),

        ])
        payment_count = Payments.sudo().search_count([('partner_id', '=', partner.id)])
        values.update({
            'employee_count': employee_count,
            'payment_count': payment_count,
        })
        return values

    @http.route(['/my/employees', '/my/employees/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_employees(self, page=1, date_begin=None, date_end=None, sortby=None, search=None,
                            search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        if not partner.last_client_id and partner.client_contact_rel_ids:
            partner.sudo().write({'last_client_id': partner.client_contact_rel_ids[0].client_id.id})
        Employees = request.env['hr.employee']
        domain = [
            ('partner_parent_id', '=', partner.last_client_id.id),
        ]
        searchbar_sortings = {
            'name': {'label': _('Reference'), 'order': 'name'},
            'qid_no': {'label': _('QID No'), 'order': 'qid_no'},
            'passport_id': {'label': _('Passport No'), 'order': 'passport_id'},
            'sponsor': {'label': _('Sponsor'), 'order': 'sponsor'},
            'stage': {'label': _('State'), 'order': 'state'},
        }
        searchbar_inputs = {
            'status': {'input': 'state', 'label': _('Status')},
            'name': {'input': 'name', 'label': _('Name')},
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
        }
        # default sortby order
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['order']

        s_domain = []
        if search and search_in:
            search_domain = []
            if search_in == 'state':
                search_domain = OR([search_domain, [('state', 'ilike', search)]])
            if search_in == 'name':
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in == 'content':
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('state', 'ilike', search)]])
            domain += search_domain
        # count for pager
        employee_count = Employees.sudo().search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/employees",
            total=employee_count,
            page=page,
            step=10
        )
        # search the count to display, according to the pager data
        employees = Employees.sudo().search(domain, order=sort_order, limit=10, offset=pager['offset'])
        request.session['employee_history'] = employees.ids[:100]
        employee_ids = request.env['hr.employee'].sudo().search([])
        all_services = request.env['ebs.crm.service'].sudo().search([], order='category_id')
        nationalities = request.env['res.country'].sudo().search([])
        job_positions = request.env['hr.job'].sudo().search([])
        related_clients = request.env['ebs.client.contact'].sudo().search([('partner_id', '=', partner.id)]).mapped(
            'client_id')
        client_contracts = request.env['ebs.crm.proposal'].sudo().search(
            [('contact_id', '=', partner.last_client_id.id), ('type', '=', 'proposal')])
        client_employee_ids = request.env['hr.employee'].sudo().search(
            [('partner_parent_id', '=', partner.last_client_id.id)])

        values.update({
            'date': date_begin,
            'employees': employees,
            'page_name': 'employee',
            'pager': pager,
            'default_url': '/my/employees',
            'searchbar_sortings': searchbar_sortings,
            'last_client_id': partner.last_client_id.id,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search': search,
            'search_in': search_in,
            'employee_ids': employee_ids,
            'all_services': all_services,
            'client_employee_ids': client_employee_ids,
            'nationalities': nationalities,
            'job_positions': job_positions,
            'related_clients': related_clients,
            'client_contracts': client_contracts,
        })
        return request.render("ebs_fusion_theme.portal_my_employees", values)

    @http.route(['/my/employees/<int:order_id>'], type='http', auth="user", website=True)
    def portal_employees(self, order_id, report_type=None, access_token=None, message=False, download=False,
                         **kw):
        try:
            employee_sudo = self._document_check_access('hr.employee', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if employee_sudo and request.session.get(
                'view_quote_%s' % employee_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % employee_sudo.id] = now
            body = _('Employee viewed by customer %s') % employee_sudo.partner_id.name
            _message_post_helper('hr.employee', employee_sudo.id, body, token=employee_sudo.access_token,
                                 message_type='notification', subtype="mail.mt_note")

        partner = request.env.user.partner_id

        if not partner.last_client_id and partner.client_contact_rel_ids:
            partner.sudo().write({'last_client_id': partner.client_contact_rel_ids[0].client_id.id})
        related_clients = request.env['ebs.client.contact'].sudo().search([('partner_id', '=', partner.id)]).mapped(
            'client_id')
        client_contracts = request.env['ebs.crm.proposal'].sudo().search(
            [('contact_id', '=', partner.last_client_id.id), ('type', '=', 'proposal')])
        documents = request.env['documents.document'].sudo().search(
            [('employee_id', '=', employee_sudo.id), ('employee_id', '!=', False)])
        dependent_ids = request.env['res.partner'].sudo().search([('parent_id', '=', employee_sudo.user_partner_id.id)])

        values = {
            'employee': employee_sudo,
            'documents': documents,
            'dependent_ids': dependent_ids,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': employee_sudo.partner_id.id,
            'related_clients': related_clients,
            'last_client_id': partner.last_client_id.id,
            'client_contracts': client_contracts,
            'report_type': 'html',
            'action': request.env.ref('hr.open_view_employee_list_my'),
        }

        return request.render('ebs_fusion_theme.employee_portal_template', values)

    @http.route(['/my/dependent/<int:order_id>'], type='http', auth="user", website=True)
    def portal_dependent(self, report_type=None, access_token=None, message=False, download=False, **kw):
        dependent_sudo = request.env['res.partner'].sudo().browse(kw.get('order_id'))
        documents = request.env['documents.document'].sudo().search(
            [('partner_id', '=', dependent_sudo.id), ('partner_id', '!=', False)])

        values = {
            'dependent_id': dependent_sudo,
            'documents': documents,
        }

        return request.render('ebs_fusion_theme.dependent_portal_template', values)

    def _prepare_dashboard_layout_values(self):
        partner = request.env.user.partner_id
        total_services_count = request.env['ebs.crm.service.process'].sudo().search_count(
            [('partner_id', '=', partner.id)])
        pending_services_count = request.env['ebs.crm.service.process'].sudo().search_count(
            [('partner_id', '=', partner.id), ('status', '=', 'onhold')])
        active_services_count = request.env['ebs.crm.service.process'].sudo().search_count(
            [('partner_id', '=', partner.id), ('status', '=', 'ongoing')])
        closed_services_count = request.env['ebs.crm.service.process'].sudo().search_count(
            [('partner_id', '=', partner.id), ('status', '=', 'completed')])

        # Notification Data
        mail_messages = []
        service_process_ids = request.env['ebs.crm.service.process'].sudo().search([('partner_id', '=', partner.id)])
        for process in service_process_ids:
            mail_message_ids = request.env['mail.message'].sudo().search(
                [('model', '=', 'ebs.crm.service.process'), ('res_id', '=', process.id), ('messages_read', '=', False)])
            for message in mail_message_ids:
                if message.body:
                    mail_messages.append({'body': message.body[3:-4], 'id': message.id})
        values = {
            'total_count': total_services_count,
            'active_count': active_services_count,
            'pending_count': pending_services_count,
            'closed_count': closed_services_count,
            'notifications': mail_messages,
        }
        return values

    @http.route(['/next/service'], type='http', auth="user", website=True)
    def next_page(self, **kw):
        values = self._prepare_dashboard_layout_values()
        if kw.get('next_page'):
            next_number = int(kw.get('next_page'))
            partner = request.env.user.partner_id
            if next_number:
                services = request.env['ebs.crm.service.process'].sudo().search(
                    [('id', '>', next_number), ('partner_id', '=', partner.id)], limit=5)
                previous_page_number = None
                next_page_number = None
                services = services.sorted(key=lambda r: r.id)
                if services:
                    previous_page_number = services[0]
                    next_page_number = services[-1]
                    previous_have = request.env['ebs.crm.service.process'].sudo().search(
                        [('id', '<', previous_page_number.id), ('partner_id', '=', partner.id)],
                        limit=5)
                    next_have = request.env['ebs.crm.service.process'].sudo().search(
                        [('id', '>', next_page_number.id), ('partner_id', '=', partner.id)], limit=5)
                    values.update({
                        'services': services,
                    })
                    if previous_have:
                        values.update({
                            'previous_page_number': previous_page_number.id,
                        })

                    if next_have:
                        values.update({
                            'next_page_number': next_page_number.id,
                        })
            return request.render("ebs_fusion_theme.portal_my_home_dashboard", values)
        else:
            return request.redirect('/my/home')

    @http.route(['/previous/service'], type='http', auth="user", website=True)
    def previous_page(self, **kw):
        values = self._prepare_dashboard_layout_values()
        if kw.get('previous_page'):
            previous_number = int(kw.get('previous_page'))
            partner = request.env.user.partner_id.id
            if previous_number:
                services = request.env['ebs.crm.service.process'].sudo().search(
                    [('id', '<', previous_number), ('partner_id', '=', partner)], limit=5, order="id desc")
                previous_page_number = None
                next_page_number = None
                services = services.sorted(key=lambda r: r.id)
                if services:
                    previous_page_number = services[0]
                    next_page_number = services[-1]
                    previous_have = request.env['ebs.crm.service.process'].sudo().search(
                        [('id', '<', previous_page_number.id), ('partner_id', '=', partner)], limit=5)
                    next_have = request.env['ebs.crm.service.process'].sudo().search(
                        [('id', '>', next_page_number.id), ('partner_id', '=', partner)], limit=5)
                    values.update({
                        'services': services,
                    })
                    if previous_have:
                        values.update({
                            'previous_page_number': previous_page_number.id,
                        })
                    if next_have:
                        values.update({
                            'next_page_number': next_page_number.id,
                        })
            return request.render("ebs_fusion_theme.portal_my_home_dashboard", values)
        else:
            return request.redirect('/my/home')

    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        values = self._prepare_dashboard_layout_values()
        partner = request.env.user.partner_id

        if not partner.last_client_id and partner.client_contact_rel_ids:
            partner.sudo().write({'last_client_id': partner.client_contact_rel_ids[0].client_id.id})
        services = request.env['ebs.crm.service.process'].sudo().search([('partner_id', '=', partner.id)], limit=5)
        all_services = request.env['ebs.crm.service'].sudo().search([], order='category_id')
        employee_ids = request.env['hr.employee'].sudo().search([])
        nationalities = request.env['res.country'].sudo().search([])
        job_positions = request.env['hr.job'].sudo().search([])
        related_clients = request.env['ebs.client.contact'].sudo().search([('partner_id', '=', partner.id)]).mapped(
            'client_id')
        client_contracts = request.env['ebs.crm.proposal'].sudo().search(
            [('contact_id', '=', partner.last_client_id.id), ('type', '=', 'proposal')])

        previous_page_number = None
        next_page_number = None
        if services:
            next_page_number = services[-1]
            next_have = request.env['ebs.crm.service.process'].sudo().search(
                [('id', '>', next_page_number.id), ('partner_id', '=', partner.id)], limit=5)
            values.update({
                'previous_page_number': previous_page_number,
            })
            if next_have:
                values.update({
                    'next_page_number': next_page_number.id,
                })
        client_employee_ids = request.env['hr.employee'].sudo().search(
            [('partner_parent_id', '=', partner.last_client_id.id)])
        values.update({
            'services': services,
            'all_services': all_services,
            'client_employee_ids': client_employee_ids,
            'employee_ids': employee_ids,
            'nationalities': nationalities,
            'last_client_id': partner.last_client_id.id,
            'job_positions': job_positions,
            'related_clients': related_clients,
            'client_contracts': client_contracts,
            'page_name': 'home'
        })

        return request.render("ebs_fusion_theme.portal_my_home_dashboard", values)

    @http.route(['/my/document'], type='http', auth="user", website=True)
    def my_profile(self, **kw):
        values = self._prepare_portal_layout_values()
        return request.render("portal.portal_my_home", values)

    @http.route(['/search/notification/<int:notification_id>'], type='http', auth="public", website=True)
    def notification_read(self, **kw):
        notification_id = kw.get('notification_id')
        if notification_id:
            message = request.env['mail.message'].sudo().search([('id', '=', int(notification_id))])
            message.sudo().write({'messages_read': True})
            return request.redirect('/my/home')
        return request.redirect('/my/home')

    @http.route(['/registration'], type='http', auth="user", website=True)
    def start_registration(self, **kw):

        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id

        payment_terms = request.env['account.payment.term'].sudo().search([])
        commercial_reg_status = request.env['commercial.reg.status'].sudo().search([])
        legal_forms = request.env['cr.legal.form'].sudo().search([])
        est_sectors = request.env['est.sector'].sudo().search([])
        all_services = request.env['ebs.crm.service'].sudo().search([], order='category_id')
        secondary_person = client_id.secondary_contact_child_ids
        primary_person = client_id.contact_child_ids
        nationalities = request.env['res.country'].sudo().search([])
        client_contracts = request.env['ebs.crm.proposal'].sudo().search(
            [('contact_id', '=', client_id.id), ('type', '=', 'proposal')])

        commercial_registration_document = client_id.cr_document_id
        commercial_license_document = client_id.cl_document_id
        cr_managers_ids = commercial_registration_document.cr_managers_ids
        establishment_card_document = client_id.ec_document_id
        if not establishment_card_document:
            cr_authorizers_ids = commercial_registration_document.cr_managers_ids
        else:
            cr_authorizers_ids = establishment_card_document.cr_authorizers_ids
        cr_business_activities_ids = commercial_registration_document.cr_business_activities_ids

        partners = commercial_registration_document.cr_partner_ids
        sub_service_mapping = {}
        group_services = request.env['ebs.crm.service'].sudo().search([('is_group', '=', True)])
        client_lead_id = request.env['crm.lead'].sudo().search([('partner_id', '=', client_id.id)], limit=1)
        if not client_lead_id:
            raise UserWarning("There is no opportunity linked to this client")
        opportunity_type_service_mapping_ids = client_lead_id.opportunity_type_service_mapping_ids
        checked_services = opportunity_type_service_mapping_ids.service_id.ids
        new_service_option_line = opportunity_type_service_mapping_ids.filtered(
            lambda o: o.service_option_id.name == 'new' and o.state != 'rejected')
        renew_service_option_line = opportunity_type_service_mapping_ids.filtered(
            lambda o: o.service_option_id.name == 'renew' and o.state != 'rejected')
        manage_service_option_line = opportunity_type_service_mapping_ids.filtered(
            lambda o: o.service_option_id.name == 'manage' and o.state != 'rejected')
        national_address = client_id.child_ids.filtered(lambda o: o.address_type == 'national_address')
        employee_ids = request.env['hr.employee'].sudo().search([])
        service_status_list = []
        for rec in new_service_option_line:
            service_status_list.append({rec.service_id.id: {rec.service_option_id.name: rec.state}})
        for rec in renew_service_option_line:
            service_status_list.append({rec.service_id.id: {rec.service_option_id.name: rec.state}})
        for rec in manage_service_option_line:
            service_status_list.append({rec.service_id.id: {rec.service_option_id.name: rec.state}})

        job_positions = request.env['hr.job'].sudo().search([])
        business_activities = request.env['business.activities'].sudo().search([])
        tax_cards = request.env['documents.document'].sudo().search([('document_type_name', '=', 'Tax Card')])
        related_clients = request.env['ebs.client.contact'].sudo().search([('partner_id', '=', partner_id.id)]).mapped(
            'client_id')
        zones = request.env['ebs.na.zone'].sudo().search([])
        streets = request.env['ebs.na.street'].sudo().search([])
        buildings = request.env['ebs.na.building'].sudo().search([])

        for service in group_services:
            sub_service_mapping.update({service.id: service.sudo().dependent_services_ids})
        client_employee_ids = request.env['hr.employee'].sudo().search(
            [('partner_parent_id', '=', client_id.id)])
        values = {
            'checked_services': checked_services,
            'group_services': group_services,
            'opportunity_service_lines': opportunity_type_service_mapping_ids.filtered(
                lambda o: o.state != 'rejected').mapped('service_id'),
            'all_services': all_services - opportunity_type_service_mapping_ids.mapped('service_id'),
            'client_employee_ids': client_employee_ids,
            'related_clients': related_clients,
            'tax_cards': tax_cards,
            'new_service_option_line': new_service_option_line,
            'renew_service_option_line': renew_service_option_line,
            'manage_service_option_line': manage_service_option_line,
            'business_activities': business_activities,
            'service_option_dict': service_status_list,
            'sub_service_mapping': sub_service_mapping,
            'primary_contact': partner_id,
            'national_address': national_address[0] if len(national_address) > 0 else national_address,
            'payment_terms': payment_terms,
            'commercial_reg_status': commercial_reg_status,
            'legal_forms': legal_forms,
            'est_sectors': est_sectors,
            'last_client_id': client_id.id,
            'nationalities': nationalities,
            'commercial_registration_document': commercial_registration_document,
            'commercial_license_document': commercial_license_document,
            'establishment_card_document': establishment_card_document,
            'managers': cr_managers_ids,
            'authorisers': cr_authorizers_ids,
            'cr_business_activities_ids': cr_business_activities_ids,
            'partners': partners,
            'client': client_id,
            'permissions': [{'name': 'Approver', 'value': 'approver'}, {'name': 'Requester', 'value': 'requester'}],
            'secondary_other_person': secondary_person,
            'primary_other_person': primary_person,
            'employee_ids': employee_ids,
            'job_positions': job_positions,
            'error_msg': client_id.website_error_msg,
            'zones': zones,
            'streets': streets,
            'buildings': buildings,
        }
        if client_contracts:
            values.update({
                'client_contracts': client_contracts
            })

        if request.httprequest.full_path == "/registration?":
            if not client_id.is_user_information:
                return request.redirect('/registration?user_info=true')
            elif not client_id.is_commercial_registration:
                return request.redirect('/registration?ui=true')
            elif not client_id.is_commercial_license:
                return request.redirect('/registration?cr=true')
            elif not client_id.is_establishment_card:
                return request.redirect('/registration?cl=true')
            elif not client_id.is_national_address:
                return request.redirect('/registration?ec=true')
            elif not client_id.is_services_submit:
                return request.redirect('/registration?na=true')
            elif client_id.is_summary:
                return request.redirect('/registration?summary=true')
            elif client_id.is_form_submit:
                return request.redirect('/registration?submitted=true')
        return request.render("ebs_fusion_theme.registration", values)

    @http.route(['/get/job_positions'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_job_positions(self, **kw):
        job_positions = request.env['hr.job'].sudo().search([])
        return {
            'jobs': [(job.id, job.name) for job in job_positions],
        }

    @http.route(['/get/street'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_street(self, **kw):
        if kw.get('zone'):
            streets = request.env['ebs.na.street'].sudo().search([('zone_id', '=', int(kw.get('zone')))])
            return {
                'streets': [(street.id, street.name) for street in streets],
            }
        else:
            return {
                'streets': []
            }

    @http.route(['/get/building'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_building(self, **kw):
        if kw.get('street'):
            buildings = request.env['ebs.na.building'].sudo().search([('street_id', '=', int(kw.get('street')))])
            return {
                'buildings': [(building.id, building.name) for building in buildings],
            }
        else:
            return {
                'buildings': []
            }

    @http.route(['/add/service_opportunity'], type='json', auth="public", methods=['POST'],
                website=True)
    def add_service_to_opportunity(self, **kw):
        option_dict = {}
        options = [k for k, v in kw.items() if v == True]
        client_id = request.env.user.partner_id.last_client_id
        lead_id = request.env['crm.lead'].sudo().search([('partner_id', '=', client_id.id)], limit=1)
        service_id = request.env['ebs.crm.service'].browse([int(kw.get('service'))])
        new_option_line = service_id.service_option_ids.filtered(lambda o: o.name == 'new')
        if new_option_line:
            option_dict.update({'new': True if 'new' in options else False})
        renew_option_line = service_id.service_option_ids.filtered(lambda o: o.name == 'renew')
        if renew_option_line:
            option_dict.update({'renew': True if 'renew' in options else False})
        manage_option_line = service_id.service_option_ids.filtered(lambda o: o.name == 'manage')
        if manage_option_line:
            option_dict.update({'manage': True if 'manage' in options else False})
        if service_id.id in lead_id.opportunity_type_service_mapping_ids.mapped('service_id').ids:
            return False
        elif kw.get('service'):
            for option in options:
                service_option_id = service_id.service_option_ids.filtered(lambda o: o.name == option)
                lead_id.sudo().write({
                    'opportunity_type_service_mapping_ids': [(0, 0, {
                        'service_id': int(kw.get('service')),
                        'service_option_id': service_option_id.id,
                        'govt_fees': service_option_id.govt_fees,
                        'fusion_fees': service_option_id.fusion_fees,
                    })]
                })
            option_dict.update({'service': service_id.name, 'group': service_id.is_group,
                                'subservices': service_id.dependent_services_ids.mapped('service').mapped('name')})
            return option_dict
        else:
            return False

    @http.route(['/get/nationalities'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_nationalities(self, **kw):
        nationalities = request.env['res.country'].sudo().search([])
        return {
            'nationalities': [(nat.id, nat.name) for nat in nationalities],
        }

    @http.route(['/get/employee_nationality'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_selected_employee_nationality(self, **kw):
        employee = request.env['hr.employee'].sudo().browse(int(kw.get('employee')))
        return {
            'nationality': employee.nationality_id.id,
            'gender': employee.gender,
            'job_id': employee.job_id.id,
        }

    @http.route(['/get/service_ids'], type='json', auth="public", methods=['POST'], website=True)
    def get_service_ids(self, service_order_type, **kw):
        domain = [('state', '=', 'ready')]
        if service_order_type == 'company':
            domain.append(('target_audience', '=', 'company'))
        else:
            domain.append(('target_audience', '=', 'person'))
        service_ids = request.env['ebs.crm.service'].sudo().search(domain, order='category_id')
        services = [(service.id, service.name) for service in service_ids]
        return {'service_ids': services}

    @http.route(['/get/service_options'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_service_options(self, service, related_company, **kw):
        service_id = request.env['ebs.crm.service'].sudo().search([('id', '=', int(service) if service else False)])
        depend_service_ids = service_id.is_group
        depend_service_list = []
        if depend_service_ids:
            depend_service_data = service_id.dependent_services_ids.service
            for service in depend_service_data:
                depend_service_list.append(service.name)
        option_ids = []
        if related_company:
            service_option_ids = service_id.service_option_ids.filtered(
                lambda o: o.company_id.id == int(related_company))
            option_ids = [(option.id, option.display_name) for option in service_option_ids]
        return {
            'new': True if service_id.service_option_ids.filtered(lambda o: o.name == 'new') else False,
            'renew': True if service_id.service_option_ids.filtered(lambda o: o.name == 'renew') else False,
            'manage': True if service_id.service_option_ids.filtered(lambda o: o.name == 'manage') else False,
            'depend_service_list': depend_service_list,
            'option_ids': option_ids
        }

    @http.route(['/get/team_member'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_team_member(self, team, **kw):
        team_id = request.env['crm.team'].sudo().search([('id', '=', int(team) if team else False)])
        member_ids = []
        if team_id:
            member_ids = [(member.id, member.display_name) for member in team_id.member_ids]
        return {
            'member_ids': member_ids
        }

    @http.route(['/get/service_options_fees'], type='json', auth="public", methods=['POST'], website=True)
    def get_service_options_fees(self, service_option, urgent, **kw):
        service_option_id = request.env['ebs.service.option'].sudo().search(
            [('id', '=', int(service_option) if service_option else False)])
        fusion_fees = service_option_id.fusion_fees
        if urgent == 'yes':
            fusion_fees = service_option_id.fusion_fees * 2
        return {
            'govt_fees': service_option_id.govt_fees,
            'fusion_fees': fusion_fees,
        }

    @http.route(['/service_order/create'], type='http', auth="public", methods=['POST'],
                website=True, csrf=False)
    def get_service_form_data(self, **kw):
        service_id = False
        if kw.get('service_id'):
            service_id = kw.get('service_id')
        elif kw.get('service_corporate_id'):
            service_id = kw.get('service_corporate_id')
        service_obj = request.env['ebs.crm.service'].sudo().browse(int(service_id))
        depend_service_ids = service_obj.is_group

        param_company_id = int(kw.get('select_related_fusion_company'))

        # Create service orders
        partner = request.env.user.partner_id

        if not partner.last_client_id and partner.client_contact_rel_ids:
            partner.sudo().write({'last_client_id': partner.client_contact_rel_ids[0].client_id.id})
        is_service_group = request.env['ebs.crm.service']
        template_id = False
        if service_id:
            is_service_group = request.env['ebs.crm.service'].sudo().search([('id', '=', int(service_id))])
            template_id = request.env['ebs.crm.service.template'].sudo().search(
                [('service_id', '=', is_service_group.id)],
                limit=1)
        employee_id = int(kw.get('employee_id')) if kw.get('employee_id') else False
        if employee_id:
            emp_obj = request.env['hr.employee'].sudo().browse(int(kw.get('employee_id')))
        if not template_id:
            if len(is_service_group) > 1:
                is_service_group.set_ready()
                template_id = request.env['ebs.crm.service.template'].sudo().search(
                    [('select_id', '=', is_service_group.id)],
                    limit=1)
        if kw.get('select_service_order_type') == 'company':
            service_partner_id = partner.last_client_id.id
        elif kw.get('select_service_order_type') in ['employee', 'dependent']:
            service_partner_id = emp_obj.user_partner_id.id
        elif kw.get('select_service_order_type') == 'visitor':
            service_partner_id = partner.id

        create_vals = {
            'partner_id': service_partner_id,
            'client_id': partner.last_client_id.id,
            'company_id': param_company_id,
            'generated_from_portal': True,
            'service_id': int(service_id) if service_id else False,

            'service_order_type': kw.get('select_service_order_type'),
            'option_id': int(kw.get('options_id')) if kw.get('options_id') else False,
            'is_urgent': True if kw.get('urgent_id') == 'yes' else False,
        }
        if kw.get('select_service_order_type') in ['employee', 'dependent']:
            create_vals.update({'employee_id': emp_obj.id})
        account_manager = partner.last_client_id.client_account_manager_id
        if account_manager:
            create_vals.update({'assigned_user_id': account_manager.id})
        order_id = request.env['ebs.crm.service.process'].sudo().create(create_vals)
        order_id.sudo().onchange_option()
        recipient_ids = []
        if account_manager:
            recipient_ids.append((4, account_manager.id))
        else:
            users = request.env['res.users'].sudo().search(
                [("share", '=', False), ("company_id", "=", param_company_id)])
            for user in users:
                if user.has_group(
                        'ebs_fusion_services.group_services_manager') and order_id.company_id.id in user.company_ids.ids:
                    recipient_ids.append((4, user.partner_id.id))
        if recipient_ids:
            smtp = request.env['ir.mail_server'].sudo().search([('name', '=', 'Info.system')])
            if smtp:
                subject = 'Service Order Request'
                body = '<p>The Service order is requested by %s with company %s and service %s.</p>' % (
                    partner.name, order_id.company_id.name, order_id.service_id.name)
                order_id.send_service_order_mail(subject, body, recipient_ids)
        return request.redirect('/my/service_orders/%s' % order_id.id)

    def create_national_address_section(self, kw, client_id):
        national_address = client_id.child_ids.filtered(lambda o: o.address_type == 'national_address')
        if national_address:
            national_address[0].sudo().write({
                'zone_id': kw.get('na_zone'),
                'building_villa_name': kw.get('na_building'),
                'street_name': kw.get('na_street'),
                'building_villa_no': kw.get('na_unit'),
            })
        else:
            client_id.sudo().write({'child_ids': [(0, 0, {
                'address_type': 'national_address',
                'active': True,
                'name': kw.get('na_street'),
                'type': 'other',
                'zone_id': kw.get('na_zone'),
                'building_villa_name': kw.get('na_building'),
                'street_name': kw.get('na_street'),
                'building_villa_no': kw.get('na_unit'),
            })]
                                    })

    def link_partner_manager(self, partner_search_ids, manager_search_ids, client_id):
        if partner_search_ids:
            for partner in partner_search_ids:
                client_contact = partner.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id == client_id.id)
                if client_contact:
                    client_contact.sudo().write({'is_shareholder': True,
                                                 'email': partner.email,
                                                 'permission': partner.permission,
                                                 })
                else:
                    partner.sudo().write({'last_client_id': client_id.id, 'client_contact_rel_ids': [
                        (0, 0, {
                            'client_id': client_id.id,
                            'is_shareholder': True,
                            'email': partner.email,
                            'permission': partner.permission,
                        })]})

        if manager_search_ids:
            for manager in manager_search_ids:
                client_contact = manager.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id == client_id.id)
                if client_contact:
                    client_contact.sudo().write({'is_manager_cr': True,
                                                 'email': manager.email,
                                                 'permission': manager.permission,
                                                 })
                else:
                    manager.sudo().write({'last_client_id': client_id.id, 'client_contact_rel_ids': [
                        (0, 0, {
                            'client_id': client_id.id,
                            'is_manager_cr': True,
                            'email': manager.email,
                            'permission': manager.permission,
                        })]})

    def make_str_to_list(self, str):
        if str:
            return [int(act) for act in eval(str)] if str else []
        return []

    def update_new_record_old(self, records):
        if records:
            for rec in records:
                rec.sudo().write({'is_newly_create': False})

    def create_commercial_registration_section(self, kw, client_id, essential_folder_id):
        # Commercial Registration Document Creation And Updation
        cr_document_type = request.env['ebs.document.type'].sudo().search(
            [('meta_data_template', '=', 'Commercial Registration (CR) Application')])
        if not cr_document_type:
            raise UserWarning('Document Type Of Commercial Registration (CR) Application Is Not Available.')
        commercial_registration_document = client_id.cr_document_id
        # Document Update

        partner_ids = self.make_str_to_list(kw.get('partner_input'))
        manager_ids = self.make_str_to_list(kw.get('manager_input'))
        partner_search_ids = False
        manager_search_ids = False
        if partner_ids:
            partner_search_ids = request.env['res.partner'].sudo().browse(partner_ids)
        if manager_ids:
            manager_search_ids = request.env['res.partner'].sudo().browse(manager_ids)
        self.update_new_record_old(partner_search_ids)
        self.update_new_record_old(manager_search_ids)

        cr_activity_ids_before_main_document_save = commercial_registration_document.cr_business_activities_ids
        if commercial_registration_document:
            cr_attachment_id = commercial_registration_document.attachment_id
            if kw['commercial_registration_file']:
                cr_file = kw['commercial_registration_file']
                cr_attachment_id = self.create_passport_qid_document(client_id, cr_file)
            commercial_registration_document.sudo().write({

                'attachment_id': cr_attachment_id.id,
                'document_number': kw['commercial_reg_no'],
                'partner_id': client_id.id,
                'cr_reg_no': kw['commercial_reg_no'],
                'cr_tax_reg_no': int(kw['tax_reg_no']) if kw['tax_reg_no'] else False,
                'cr_trade_name': kw['trade_name'],
                'arabic_name': kw['trade_name_ar'],
                'cr_creation_date': parse(kw['creation_date']) if kw['creation_date'] else None,
                'cr_legal_form': int(kw['legal_form']) if kw['legal_form'] else False,
                'cr_capital': kw['capital'] or False,
                'cr_reg_status': int(kw['commercial_reg_status']) if kw['commercial_reg_status'] else False,
                'nationality': int(kw['firm_nationality']) if kw['firm_nationality'] else False,
                'cr_no_brances': kw['no_of_branches'] or False,
                'cr_partner_ids': [(6, 0, partner_ids + commercial_registration_document.cr_partner_ids.ids)],
                'cr_managers_ids': [(6, 0, manager_ids + commercial_registration_document.cr_managers_ids.ids)],
            })
        # Document Create
        else:
            if kw['commercial_registration_file']:
                cr_file = kw['commercial_registration_file']
                cr_attachment_id = self.create_passport_qid_document(client_id, cr_file)
                commercial_registration_document = request.env['documents.document'].sudo().create({

                    'attachment_id': cr_attachment_id.id,
                    'document_number': kw['commercial_reg_no'],
                    'folder_ids': [(6, 0, cr_document_type.folder_ids.ids)],
                    'folder_id': essential_folder_id.id,
                    'document_type_id': cr_document_type.id,
                    'partner_id': client_id.id,
                    'cr_reg_no': kw['commercial_reg_no'],
                    'cr_tax_reg_no': int(kw['tax_reg_no']) if kw['tax_reg_no'] else False,
                    'cr_trade_name': kw['trade_name'],
                    'arabic_name': kw['trade_name_ar'],
                    'cr_creation_date': parse(kw['creation_date']) if kw['creation_date'] else None,
                    'cr_legal_form': int(kw['legal_form']) if kw['legal_form'] else False,
                    'cr_capital': kw['capital'] or False,
                    'cr_reg_status': int(kw['commercial_reg_status']) if kw['commercial_reg_status'] else False,
                    'nationality': int(kw['firm_nationality']) if kw['firm_nationality'] else False,
                    'cr_no_brances': kw['no_of_branches'] or False,
                    'cr_partner_ids': [(6, 0, partner_ids)],
                    'cr_managers_ids': [(6, 0, manager_ids)],
                })

                if not commercial_registration_document.cr_business_activities_ids and kw.get('activity_hidden_ids'):
                    if kw.get('activity_hidden_ids'):
                        activities_list = [int(act) for act in eval(kw.get('activity_hidden_ids'))]
                    commercial_registration_document.sudo().write(
                        {'cr_business_activities_ids': [(6, 0, activities_list)]})
                client_id.sudo().write(
                    {'arabic_name': kw['trade_name_ar'], 'cr_document_id': commercial_registration_document.id})

    def create_commercial_license_section(self, kw, client_id, primary_contact, people_folder_id,
                                          passport_document_type, qid_document_type, essential_folder_id):
        # Commercial Licence Document Creation And Updation
        cl_document_type = request.env['ebs.document.type'].sudo().search(
            [('meta_data_template', '=', 'Commercial License')])
        if not cl_document_type:
            raise UserWarning('Document Type Of Commercial Licence Is Not Available.')
        commercial_license_document = client_id.cl_document_id
        # Document Update
        if not commercial_license_document:
            commercial_license_document = request.env['documents.document'].sudo().create({
                'folder_ids': [(6, 0, cl_document_type.folder_ids.ids)],
                'folder_id': essential_folder_id.id,
                'document_type_id': cl_document_type.id,
                'partner_id': client_id.id,
                'cl_name': kw.get('cl_name'),
                'arabic_name': kw.get('cl_name_ar'),
            })
            client_id.sudo().write({'cl_document_id': commercial_license_document.id})
        if commercial_license_document:
            cl_attachment_id = commercial_license_document.attachment_id
            if kw['commercial_license_file']:
                cl_file = kw['commercial_license_file']
                cl_attachment_id = self.create_passport_qid_document(primary_contact, cl_file)
            cl_partner_id = False
            if kw.get('license_number'):
                passport_document_type = request.env['ebs.document.type'].sudo().search(
                    [('meta_data_template', '=', 'Passport')])
                if not passport_document_type:
                    raise UserWarning('Document Type Of Passport Is Not Available.')
                qid_document_type = request.env['ebs.document.type'].sudo().search([('meta_data_template', '=', 'QID')])
                if not qid_document_type:
                    raise UserWarning('Document Type Of QID Is Not Available.')
                passport_file = kw.get('manager_in_charge_passport_document')
                qid_file = kw.get('manager_in_charge_qid_document')
                cl_partner_id = commercial_license_document.cl_partner_id
                if cl_partner_id:
                    update_vals_partner_manager = {}
                    if kw.get('manager_qid_radio') == 'no':
                        update_vals_partner_manager.update(
                            self.commercial_license_vals_create_update_qid_radio_no(kw, client_id))
                    elif kw.get('manager_qid_radio') == 'yes':
                        update_vals_partner_manager.update(
                            self.commercial_license_vals_create_update_qid_radio_yes(kw, client_id))
                    cl_partner_id.sudo().write(update_vals_partner_manager)
                    passport_document = request.env['documents.document'].sudo().search(
                        [('partner_id', '=', cl_partner_id.id),
                         ('document_type_id', '=',
                          passport_document_type.id)],
                        limit=1)
                    if passport_document and kw.get('manager_qid_radio') == 'no':
                        if passport_file:
                            passport_attachment_id = self.create_passport_qid_document(cl_partner_id, passport_file)
                            passport_document.sudo().write(
                                {'attachment_id': passport_attachment_id.id})
                        passport_document.sudo().write({
                            'document_number': kw.get('manager_in_charge_passport'),
                            'passport_no': kw.get('manager_in_charge_passport') or False,
                            'gender': kw.get('manager_in_charge_gender') or False,
                            'arabic_name': kw.get('manager_in_charge_name_ar') or False,
                            'passport_name': kw.get('manager_in_charge_name') or False,
                            'passport_type': kw.get('manager_in_charge_passport_type') or False,
                            'expiry_date': parse(kw.get('manager_in_charge_expiry_date')) if kw.get(
                                'manager_in_charge_expiry_date') else None,
                            'issue_date': parse(kw.get('manager_in_charge_date_of_issue')) if kw.get(
                                'manager_in_charge_date_of_issue') else None,
                            'date_of_birth': parse(kw.get('manager_in_charge_birth_date')) if kw.get(
                                'manager_in_charge_birth_date') else None,
                            'country_passport_id': int(kw.get('manager_in_charge_nationality')) if kw.get(
                                'manager_in_charge_nationality') else False,
                        })
                    elif not passport_document and kw.get('manager_qid_radio') == 'no':
                        if passport_file:
                            passport_attachment_id = self.create_passport_qid_document(cl_partner_id, passport_file)
                            passport_document = request.env['documents.document'].sudo().create({

                                'attachment_id': passport_attachment_id.id,
                                'document_number': kw.get('manager_in_charge_passport'),
                                'folder_ids': [(6, 0, passport_document_type.folder_ids.ids)],
                                'folder_id': people_folder_id.id,
                                'document_type_id': passport_document_type.id,
                                'partner_id': cl_partner_id.id,
                                'passport_no': kw.get('manager_in_charge_passport') or False,
                                'gender': kw.get('gender_extra_contact') or False,
                                'arabic_name': kw.get('manager_in_charge_name_ar') or False,
                                'passport_name': kw.get('manager_in_charge_name') or False,
                                'passport_type': kw.get('manager_in_charge_passport_type') or False,
                                'expiry_date': parse(kw.get('manager_in_charge_expiry_date')) if kw.get(
                                    'manager_in_charge_expiry_date') else None,
                                'issue_date': parse(kw.get('manager_in_charge_date_of_issue')) if kw.get(
                                    'manager_in_charge_date_of_issue') else None,
                                'date_of_birth': parse(kw.get('manager_in_charge_birth_date')) if kw.get(
                                    'manager_in_charge_birth_date') else None,
                                'country_passport_id': int(kw.get('manager_in_charge_nationality')) if kw.get(
                                    'manager_in_charge_nationality') else False,
                            })
                            cl_partner_id.sudo().write({'ps_passport_serial_no_id': passport_document.id})
                    # Update QID document
                    qid_document = request.env['documents.document'].sudo().search(
                        [('partner_id', '=', cl_partner_id.id),
                         ('document_type_id', '=',
                          qid_document_type.id)], limit=1)
                    if qid_document and kw.get('manager_qid_radio') == 'yes':
                        if qid_file:
                            qid_attachment_id = self.create_passport_qid_document(cl_partner_id, qid_file)
                            qid_document.sudo().write({'attachment_id': qid_attachment_id.id})
                        qid_document.sudo().write({
                            'document_number': kw.get('manager_in_charge_qid'),
                            'arabic_name': kw.get('manager_in_charge_name_ar') or False,
                            'job_title': int(kw.get('manager_in_charge_job_position')) if kw.get(
                                'manager_in_charge_job_position') else False,
                            'qid_name': kw.get('manager_in_charge_name') or False,
                            'expiry_date': parse(kw.get('manager_in_charge_qid_expiry_date')) if kw.get(
                                'manager_in_charge_qid_expiry_date') else None,
                            'date_of_birth': parse(kw.get('manager_in_charge_qid_birth_date')) if kw.get(
                                'manager_in_charge_qid_birth_date') else None,
                            'residency_type': kw.get('manager_in_charge_residency_type') or False,
                            'country_passport_id': int(kw.get('manager_in_charge_qid_nationality')) if kw.get(
                                'manager_in_charge_qid_nationality') else False,
                        })
                    elif not qid_document and kw.get('manager_qid_radio') == 'yes':
                        if qid_file:
                            qid_attachment_id = self.create_passport_qid_document(cl_partner_id, qid_file)
                            qid_document = request.env['documents.document'].sudo().create({

                                'attachment_id': qid_attachment_id.id,
                                'document_number': kw.get('manager_in_charge_qid') or False,
                                'folder_ids': [(6, 0, qid_document_type.folder_ids.ids)],
                                'folder_id': people_folder_id.id,
                                'document_type_id': qid_document_type.id,
                                'partner_id': cl_partner_id.id,
                                'arabic_name': kw.get('manager_in_charge_name_ar') or False,
                                'job_title': int(kw.get('manager_in_charge_job_position')) if kw.get(
                                    'manager_in_charge_job_position') else False,
                                'qid_name': kw.get('manager_in_charge_name') or False,
                                'expiry_date': parse(kw.get('manager_in_charge_qid_expiry_date')) if kw.get(
                                    'manager_in_charge_qid_expiry_date') else None,
                                'date_of_birth': parse(kw.get('manager_in_charge_qid_birth_date')) if kw.get(
                                    'manager_in_charge_qid_birth_date') else None,
                                'residency_type': kw.get('manager_in_charge_residency_type') or False,
                                'country_passport_id': int(kw.get('manager_in_charge_qid_nationality')) if kw.get(
                                    'manager_in_charge_qid_nationality') else False,
                            })
                            cl_partner_id.sudo().write({'qid_residency_id': qid_document.id})
                else:
                    create_vals_manager = {}
                    if kw.get('manager_qid_radio') == 'no':
                        create_vals_manager.update(
                            self.commercial_license_vals_create_update_qid_radio_no(kw, client_id))
                    elif kw.get('manager_qid_radio') == 'yes':
                        create_vals_manager.update(
                            self.commercial_license_vals_create_update_qid_radio_yes(kw, client_id))
                    cl_partner_id = request.env['res.partner'].sudo().create(create_vals_manager)

                    manager_in_charge_vals = {}
                    if kw.get('manager_qid_radio') == 'no' and passport_file:
                        passport_attachment_id = self.create_passport_qid_document(cl_partner_id, passport_file)
                        passport_document = request.env['documents.document'].sudo().create({

                            'attachment_id': passport_attachment_id.id,
                            'document_number': kw.get('manager_in_charge_passport'),
                            'folder_ids': [(6, 0, passport_document_type.folder_ids.ids)],
                            'folder_id': people_folder_id.id,
                            'document_type_id': passport_document_type.id,
                            'partner_id': cl_partner_id.id,
                            'passport_no': kw.get('manager_in_charge_passport') or False,
                            'gender': kw.get('gender_extra_contact') or False,
                            'arabic_name': kw.get('manager_in_charge_name_ar') or False,
                            'passport_name': kw.get('manager_in_charge_name') or False,
                            'passport_type': kw.get('manager_in_charge_passport_type') or False,
                            'expiry_date': parse(kw.get('manager_in_charge_expiry_date')) if kw.get(
                                'manager_in_charge_expiry_date') else None,
                            'issue_date': parse(kw.get('manager_in_charge_date_of_issue')) if kw.get(
                                'manager_in_charge_date_of_issue') else None,
                            'date_of_birth': parse(kw.get('manager_in_charge_birth_date')) if kw.get(
                                'manager_in_charge_birth_date') else None,
                            'country_passport_id': int(kw.get('manager_in_charge_nationality')) if kw.get(
                                'manager_in_charge_nationality') else False,
                        })
                        manager_in_charge_vals.update({'ps_passport_serial_no_id': passport_document.id})

                    if qid_file and kw.get('manager_qid_radio') == 'yes':
                        qid_attachment_id = self.create_passport_qid_document(cl_partner_id, qid_file)
                        qid_document = request.env['documents.document'].sudo().create({

                            'attachment_id': qid_attachment_id.id,
                            'document_number': kw.get('manager_in_charge_qid') or False,
                            'folder_ids': [(6, 0, qid_document_type.folder_ids.ids)],
                            'folder_id': people_folder_id.id,
                            'document_type_id': qid_document_type.id,
                            'partner_id': cl_partner_id.id,
                            'arabic_name': kw.get('manager_in_charge_name_ar') or False,
                            'job_title': int(kw.get('manager_in_charge_job_position')) if kw.get(
                                'manager_in_charge_job_position') else False,
                            'qid_name': kw.get('manager_in_charge_name') or False,
                            'expiry_date': parse(kw.get('manager_in_charge_qid_expiry_date')) if kw.get(
                                'manager_in_charge_qid_expiry_date') else None,
                            'date_of_birth': parse(kw.get('manager_in_charge_qid_birth_date')) if kw.get(
                                'manager_in_charge_qid_birth_date') else None,
                            'residency_type': kw.get('manager_in_charge_residency_type') or False,
                            'country_passport_id': int(kw.get('manager_in_charge_qid_nationality')) if kw.get(
                                'manager_in_charge_qid_nationality') else False,
                        })
                        manager_in_charge_vals.update({'qid_residency_id': qid_document.id})
                    if manager_in_charge_vals:
                        cl_partner_id.sudo().write(manager_in_charge_vals)

            commercial_license_document.sudo().write({
                'attachment_id': cl_attachment_id.id,
                'document_number': kw.get('license_number'),
                'license_number': kw.get('license_number'),
                'document_type_id': cl_document_type.id,
                'partner_id': client_id.id,
                'cl_partner_id': cl_partner_id.id if cl_partner_id else False,
                'cl_name': client_id.name,
            })

    def link_authorizer(self, authorizer_search_ids, client_id):
        if authorizer_search_ids:
            for authorizer in authorizer_search_ids:
                client_contact = authorizer.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id == client_id.id)
                if client_contact:
                    client_contact.sudo().write({'is_manager_ec': True,
                                                 'email': authorizer.email,
                                                 'permission': authorizer.permission,
                                                 })
                else:
                    authorizer.sudo().write({'last_client_id': client_id.id, 'client_contact_rel_ids': [
                        (0, 0, {
                            'client_id': client_id.id,
                            'is_manager_ec': True,
                            'email': authorizer.email,
                            'permission': authorizer.permission,
                        })]})

    def create_establishment_card_section(self, kw, client_id, essential_folder_id, primary_contact):
        # Establishment Card Document Creation And Updation
        ec_document_type = request.env['ebs.document.type'].sudo().search(
            [('meta_data_template', '=', 'Establishment Card')])
        if not ec_document_type:
            raise UserWarning('Document Type Of Establishment Card Is Not Available.')
        establishment_card_document = client_id.ec_document_id
        # Document Update
        authorizer_ids = self.make_str_to_list(kw.get('authorizer_input'))

        authorizer_search_ids = False

        if authorizer_ids:
            authorizer_search_ids = request.env['res.partner'].sudo().browse(authorizer_ids)
        self.update_new_record_old(authorizer_search_ids)

        if establishment_card_document:
            ec_file = kw['establishment_card_file']
            if ec_file:
                ec_attachment_id = self.create_passport_qid_document(primary_contact, ec_file)
                establishment_card_document.sudo().write({
                    'attachment_id': ec_attachment_id.id, })

            establishment_card_document.sudo().write({
                'document_number': kw['est_id'],
                'folder_ids': [(6, 0, ec_document_type.folder_ids.ids)],
                'folder_id': essential_folder_id.id,
                'document_type_id': ec_document_type.id,
                'partner_id': client_id.id,
                'est_id': kw['est_id'],
                'est_name_en': kw['est_name_en'],
                'arabic_name': kw['est_name_ar'],
                'est_sector': int(kw['est_sector']) if kw['est_sector'] else False,
                'est_first_issue': datetime.strptime(kw['first_issue_date'], '%d/%m/%Y') if kw[
                    'first_issue_date'] else None,
                'expiry_date': datetime.strptime(kw['est_card_expiry_date'], '%d/%m/%Y') if kw[
                    'est_card_expiry_date'] else None,
                'cr_authorizers_ids': [(6, 0, authorizer_ids + establishment_card_document.cr_authorizers_ids.ids)]
            })

        # Document Create
        else:
            if kw['establishment_card_file']:
                ec_file = kw['establishment_card_file']
                ec_attachment_id = self.create_passport_qid_document(primary_contact, ec_file)
                establishment_card_document = request.env['documents.document'].sudo().create({

                    'attachment_id': ec_attachment_id.id,
                    'document_number': kw['est_id'],
                    'folder_ids': [(6, 0, ec_document_type.folder_ids.ids)],
                    'folder_id': essential_folder_id.id,
                    'document_type_id': ec_document_type.id,
                    'partner_id': client_id.id,
                    'est_id': kw['est_id'],
                    'est_name_en': kw['est_name_en'],
                    'arabic_name': kw['est_name_ar'],
                    'est_sector': int(kw['est_sector']) if kw['est_sector'] else False,
                    'est_first_issue': parse(kw['first_issue_date']) if kw['first_issue_date'] else None,
                    'expiry_date': parse(kw['est_card_expiry_date']) if kw['est_card_expiry_date'] else None,
                    'cr_authorizers_ids': [(6, 0, authorizer_search_ids.ids if authorizer_search_ids else [])]
                })

                client_id.sudo().write({'ec_document_id': establishment_card_document.id})

    def create_service_section(self, kw, client_id):
        all_services = request.env['ebs.crm.service'].sudo().search([], order='category_id')
        lead_id = request.env['crm.lead'].sudo().search([('partner_id', '=', client_id.id)], limit=1)
        del_lines = request.env['opportunity.type.service.mapping']
        for service in all_services:
            if kw.get(service.name) and kw[service.name] == 'on':
                options = {'%s-new' % service.id: 'new', '%s-renew' % service.id: 'renew',
                           '%s-manage' % service.id: 'manage'}
                if service not in lead_id.opportunity_type_service_mapping_ids.mapped('service_id'):
                    for key, value in options.items():
                        if kw.get(key):
                            service_option_id = service.service_option_ids.filtered(lambda o: o.name == value)
                            request.env['opportunity.type.service.mapping'].sudo().create({
                                'service_id': service.id,
                                'service_option_id': service_option_id.id,
                                'govt_fees': service_option_id.govt_fees,
                                'fusion_fees': service_option_id.fusion_fees,
                                'lead_id': lead_id.id,
                            })
                else:
                    opportunity_type_service_line = request.env['opportunity.type.service.mapping'].sudo().search(
                        [('lead_id', '=', lead_id.id)])
                    for key, value in options.items():
                        line = opportunity_type_service_line.filtered(
                            lambda o: o.service_option_id.name == value and o.service_id.id == service.id)
                        if kw.get(key) and not line:
                            service_option_id = service.service_option_ids.filtered(lambda o: o.name == value)
                            request.env['opportunity.type.service.mapping'].sudo().create({
                                'service_id': service.id,
                                'service_option_id': service_option_id.id,
                                'govt_fees': service_option_id.govt_fees,
                                'fusion_fees': service_option_id.fusion_fees,
                                'lead_id': lead_id.id,
                            })
                        elif not kw.get(key) and line:
                            del_lines += line
                        else:
                            continue
            if not kw.get(service.name):
                lines = lead_id.opportunity_type_service_mapping_ids.filtered(lambda o: o.service_id.id == service.id)
                if lines:
                    del_lines += lines
        del_lines.unlink()

    def create_contract_info_section(self, kw, client_id, people_folder_id, passport_document_type, qid_document_type):
        # contract data
        if client_id and client_id.client_state == 'active':
            client_contracts = request.env['ebs.crm.proposal'].sudo().search(
                [('contact_id', '=', client_id.id), ('type', '=', 'proposal')])
            for contract in client_contracts:
                contract_start_date = kw.get('%s-contract_start_date' % (contract.id))
                contract_end_date = kw.get('%s-contract_end_date' % (contract.id))
                contract_payment_terms = kw.get('%s-contract_payment_terms' % (contract.id))
                contract_qid_document = kw.get('%s-contract_qid_document' % (contract.id))
                contract_passport_document = kw.get('%s-contract_passport_document' % (contract.id))
                contract_qid_radio = kw.get('%s-contract_qid_radio' % (contract.id))
                if contract.client_finance_id:
                    update_vals_contract = {}
                    if contract_qid_radio == "no":
                        update_vals_contract.update(self.contract_create_update_vals_qid_radio_no(kw, contract))
                        contract.client_finance_id.sudo().write(update_vals_contract)
                        if contract_passport_document or contract_qid_radio == "no":
                            if contract_passport_document:
                                passport_attachment_id = self.create_passport_qid_document(contract.client_finance_id,
                                                                                           contract_passport_document)
                                passport_document = request.env['documents.document'].sudo().create({

                                    'attachment_id': passport_attachment_id.id,
                                    'document_number': kw.get('%s-contract_passport' % (contract.id)) or False,
                                    'folder_ids': [(6, 0, passport_document_type.folder_ids.ids)],
                                    'folder_id': people_folder_id.id,
                                    'document_type_id': passport_document_type.id,
                                    'partner_id': contract.client_finance_id.id,
                                    'passport_no': kw.get('%s-contract_passport' % (contract.id)) or False,
                                    'gender': kw.get('%s-contract_gender' % (contract.id)) or False,
                                    'arabic_name': kw.get('%s-contract_name_ar' % (contract.id)) or False,
                                    'passport_name': kw.get('%s-contract_full_name' % (contract.id)) or False,
                                    'passport_type': kw.get('%s-contract_passport_type' % (contract.id)) or False,
                                    'expiry_date': parse(kw.get('%s-contract_expiry_date' % (contract.id))) if kw.get(
                                        '%s-contract_expiry_date' % (contract.id)) else None,
                                    'issue_date': parse(kw.get('%s-contract_date_of_issue' % (contract.id))) if kw.get(
                                        '%s-contract_date_of_issue' % (contract.id)) else None,
                                    'date_of_birth': parse(kw.get('%s-contract_birth_date' % (contract.id))) if kw.get(
                                        '%s-contract_birth_date' % (contract.id)) else None,
                                    'country_passport_id': int(
                                        kw.get('%s-contract_nationality' % (contract.id))) or False,
                                })
                                contract.client_finance_id.sudo().write(
                                    {'ps_passport_serial_no_id': passport_document.id})
                            elif contract.client_finance_id.ps_passport_serial_no_id:
                                contract.client_finance_id.ps_passport_serial_no_id.sudo().write({
                                    'document_number': kw.get('%s-contract_passport' % (contract.id)) or False,
                                    'passport_no': kw.get('%s-contract_passport' % (contract.id)) or False,
                                    'gender': kw.get('%s-contract_gender' % (contract.id)) or False,
                                    'arabic_name': kw.get('%s-contract_name_ar' % (contract.id)) or False,
                                    'passport_name': kw.get('%s-contract_full_name' % (contract.id)) or False,
                                    'passport_type': kw.get('%s-contract_passport_type' % (contract.id)) or False,
                                    'expiry_date': parse(kw.get('%s-contract_expiry_date' % (contract.id))) if kw.get(
                                        '%s-contract_expiry_date' % (contract.id)) else None,
                                    'issue_date': parse(kw.get('%s-contract_date_of_issue' % (contract.id))) if kw.get(
                                        '%s-contract_date_of_issue' % (contract.id)) else None,
                                    'date_of_birth': parse(kw.get('%s-contract_birth_date' % (contract.id))) if kw.get(
                                        '%s-contract_birth_date' % (contract.id)) else None,
                                    'country_passport_id': int(
                                        kw.get('%s-contract_nationality' % (contract.id))) or False,
                                })
                    if contract_qid_radio == "yes":
                        update_vals_contract.update(self.contract_create_update_vals_qid_radio_yes(kw, contract))
                        contract.client_finance_id.sudo().write(update_vals_contract)
                        if contract_qid_document or contract_qid_radio == "yes":
                            if contract_qid_document:
                                qid_attachment_id = self.create_passport_qid_document(contract.client_finance_id,
                                                                                      contract_qid_document)
                                qid_document = request.env['documents.document'].sudo().create({

                                    'attachment_id': qid_attachment_id.id,
                                    'document_number': kw.get('%s-contract_qid' % (contract.id)) or False,
                                    'folder_ids': [(6, 0, qid_document_type.folder_ids.ids)],
                                    'folder_id': people_folder_id.id,
                                    'document_type_id': qid_document_type.id,
                                    'partner_id': contract.client_finance_id.id,
                                    'arabic_name': kw.get('%s-contract_name_ar' % (contract.id)) or False,
                                    'job_title': kw.get('%s-contract_job_position' % (contract.id)) if kw.get(
                                        '%s-contract_job_position' % (contract.id)) else False,
                                    'qid_name': kw.get('%s-contract_name_english' % (contract.id)) or False,
                                    'expiry_date': parse(
                                        kw.get('%s-contract_qid_expiry_date' % (contract.id))) if kw.get(
                                        '%s-contract_qid_expiry_date' % (contract.id)) else None,
                                    'date_of_birth': parse(
                                        kw.get('%s-contract_qid_birth_date' % (contract.id))) if kw.get(
                                        '%s-contract_qid_birth_date' % (contract.id)) else None,
                                    'residency_type': kw.get('%s-contract_residency_type' % (contract.id)) or False,
                                    'country_passport_id': int(
                                        kw.get('%s-contract_qid_nationality' % (contract.id))) if kw.get(
                                        '%s-contract_qid_nationality' % (contract.id)) else False,
                                })
                                contract.client_finance_id.sudo().write({'qid_residency_id': qid_document.id})
                            elif contract.client_finance_id.qid_residency_id:
                                contract.client_finance_id.qid_residency_id.sudo().write({
                                    'document_number': kw.get('%s-contract_qid' % (contract.id)) or False,
                                    'arabic_name': kw.get('%s-contract_name_ar' % (contract.id)) or False,
                                    'job_title': kw.get('%s-contract_job_position' % (contract.id)) if kw.get(
                                        '%s-contract_job_position' % (contract.id)) else False,
                                    'qid_name': kw.get('%s-contract_name_english' % (contract.id)) or False,
                                    'expiry_date': parse(
                                        kw.get('%s-contract_qid_expiry_date' % (contract.id))) if kw.get(
                                        '%s-contract_qid_expiry_date' % (contract.id)) else None,
                                    'date_of_birth': parse(
                                        kw.get('%s-contract_qid_birth_date' % (contract.id))) if kw.get(
                                        '%s-contract_qid_birth_date' % (contract.id)) else None,
                                    'residency_type': kw.get('%s-contract_residency_type' % (contract.id)) or False,
                                    'country_passport_id': int(
                                        kw.get('%s-contract_qid_nationality' % (contract.id))) if kw.get(
                                        '%s-contract_qid_nationality' % (contract.id)) else False,

                                })
                else:
                    if contract_passport_document or contract_qid_document:
                        create_vals_contract = {}
                        if contract_qid_radio == "yes":
                            create_vals_contract.update(self.contract_create_update_vals_qid_radio_yes(kw, contract))
                        if contract_qid_radio == "no":
                            create_vals_contract.update(self.contract_create_update_vals_qid_radio_no(kw, contract))
                        contarct_partner = request.env['res.partner'].sudo().create(create_vals_contract)
                        if contract_passport_document and contract_qid_radio == 'no':
                            passport_attachment_id = self.create_passport_qid_document(contarct_partner,
                                                                                       contract_passport_document)
                            passport_document = request.env['documents.document'].sudo().create({

                                'attachment_id': passport_attachment_id.id,
                                'document_number': kw.get('%s-contract_passport' % (contract.id)) or False,
                                'folder_ids': [(6, 0, passport_document_type.folder_ids.ids)],
                                'folder_id': people_folder_id.id,
                                'document_type_id': passport_document_type.id,
                                'partner_id': contarct_partner.id,
                                'passport_no': kw.get('%s-contract_passport' % (contract.id)) or False,
                                'gender': kw.get('%s-contract_gender' % (contract.id)) or False,
                                'arabic_name': kw.get('%s-contract_name_ar' % (contract.id)) or False,
                                'passport_name': kw.get('%s-contract_full_name' % (contract.id)) or False,
                                'passport_type': kw.get('%s-contract_passport_type' % (contract.id)) or False,
                                'expiry_date': parse(kw.get('%s-contract_expiry_date' % (contract.id))) if kw.get(
                                    '%s-contract_expiry_date' % (contract.id)) else None,
                                'issue_date': parse(kw.get('%s-contract_date_of_issue' % (contract.id))) if kw.get(
                                    '%s-contract_date_of_issue' % (contract.id)) else None,
                                'date_of_birth': parse(kw.get('%s-contract_birth_date' % (contract.id))) if kw.get(
                                    '%s-contract_birth_date' % (contract.id)) else None,
                                'country_passport_id': int(kw.get('%s-contract_nationality' % (contract.id))) or False,
                            })
                            contarct_partner.sudo().write({'ps_passport_serial_no_id': passport_document.id})
                        if contract_qid_document and contract_qid_radio == 'yes':
                            qid_attachment_id = self.create_passport_qid_document(contarct_partner,
                                                                                  contract_qid_document)
                            qid_document = request.env['documents.document'].sudo().create({

                                'attachment_id': qid_attachment_id.id,
                                'document_number': kw.get('%s-contract_qid' % (contract.id)) or False,
                                'folder_ids': [(6, 0, qid_document_type.folder_ids.ids)],
                                'folder_id': people_folder_id.id,
                                'document_type_id': qid_document_type.id,
                                'partner_id': contarct_partner.id,
                                'arabic_name': kw.get('%s-contract_name_ar' % (contract.id)) or False,
                                'job_title': kw.get('%s-contract_job_position' % (contract.id)) if kw.get(
                                    '%s-contract_job_position' % (contract.id)) else False,
                                'qid_name': kw.get('%s-contract_name_english' % (contract.id)) or False,
                                'expiry_date': parse(kw.get('%s-contract_qid_expiry_date' % (contract.id))) if kw.get(
                                    '%s-contract_qid_expiry_date' % (contract.id)) else None,
                                'date_of_birth': parse(kw.get('%s-contract_qid_birth_date' % (contract.id))) if kw.get(
                                    '%s-contract_qid_birth_date' % (contract.id)) else None,
                                'residency_type': kw.get('%s-contract_residency_type' % (contract.id)) or False,
                                'country_passport_id': int(
                                    kw.get('%s-contract_qid_nationality' % (contract.id))) if kw.get(
                                    '%s-contract_qid_nationality' % (contract.id)) else False,
                            })
                            contarct_partner.sudo().write({'qid_residency_id': qid_document.id})
                        if contarct_partner:
                            contract.sudo().write({'client_finance_id': contarct_partner.id})
                contract_vals = {}
                if contract_start_date:
                    contract_vals.update({'start_date': parse(contract_start_date)})
                if contract_end_date:
                    contract_vals.update({'end_date': parse(contract_end_date)})
                if contract_payment_terms:
                    contract_vals.update({'payment_terms_id': int(contract_payment_terms)})
                contract.sudo().write(contract_vals)
                available_client_line = contract.client_finance_id.client_contact_rel_ids.filtered(
                    lambda o: o.client_id.id == client_id.id)
                if available_client_line:
                    available_client_line.sudo().write({
                        'email': kw.get('%s-contract_email' % (contract.id)),
                        'permission': kw.get('%s-contract_permission' % (contract.id)),
                        'is_client_finance_ac': True
                    })
                else:
                    contract.client_finance_id.sudo().write({'client_contact_rel_ids': [(0, 0, {
                        'email': kw.get('%s-contract_email' % (contract.id)),
                        'permission': kw.get('%s-contract_permission' % (contract.id)),
                        'client_id': client_id.id,
                        'is_client_finance_ac': True
                    })]})
                contract.sudo().write({'submitted_by_client': True})

    def create_primary_person_and_secondary_contact(self, kw, client_id):
        primary_person = []
        person = []
        if kw.get('person_input'):
            person = [int(act) for act in eval(kw.get('person_input'))]
        if kw.get('primary_person_input'):
            primary_person = [int(act) for act in eval(kw.get('primary_person_input'))]
        contact_list_primary = client_id.contact_child_ids.ids + primary_person
        contact_list = client_id.secondary_contact_child_ids.ids + person
        if contact_list_primary:
            client_id.sudo().write({'contact_child_ids': [(6, 0, contact_list_primary)]})
        if contact_list:
            client_id.sudo().write({'secondary_contact_child_ids': [(6, 0, contact_list)]})

    def redirect_url(self, name, client_id):
        if client_id.is_summary:
            return '/registration?summary=true'
        elif client_id.is_form_submit:
            return '/registration?submitted=true'
        else:
            return '/registration?' + name + '=true'

    @http.route(['/submit/registration'], type='http', auth="user", website=True)
    def submit_registration(self, **kw):
        primary_contact = request.env.user.partner_id
        if not primary_contact.last_client_id and primary_contact.client_contact_rel_ids:
            primary_contact.sudo().write({'last_client_id': primary_contact.client_contact_rel_ids[0].client_id.id})
        client_id = primary_contact.last_client_id
        try:
            people_folder_id = request.env['documents.folder'].sudo().search([('name', 'ilike', 'People')])
            essential_folder_id = request.env['documents.folder'].sudo().search([('name', 'ilike', 'Essential')])
            if not people_folder_id:
                people_folder_id = request.env['documents.folder'].sudo().create({'name': 'People'})
            if not essential_folder_id:
                company_folder_id = request.env['documents.folder'].sudo().create({'name': 'Company'})
                corporate_folder_id = request.env['documents.folder'].sudo().create({
                    'name': 'Corporate Documents',
                    'parent_folder_id': company_folder_id.id,
                })
                essential_folder_id = request.env['documents.folder'].sudo().create({
                    'name': 'Essential',
                    'parent_folder_id': corporate_folder_id.id,
                })
            passport_document_type = request.env['ebs.document.type'].sudo().search(
                [('meta_data_template', '=', 'Passport')])
            if not passport_document_type:
                raise UserWarning('Document Type Of Passport Is Not Available.')
            qid_document_type = request.env['ebs.document.type'].sudo().search([('meta_data_template', '=', 'QID')])
            if not qid_document_type:
                raise UserWarning('Document Type Of QID Is Not Available.')
            if kw.get('hidden_input_current_page_id') == 'User Information':
                self.create_primary_person_and_secondary_contact(kw, client_id)
                client_id.sudo().write({'is_user_information': True})
                name = "ui"
                return request.redirect(self.redirect_url(name, client_id))
            elif kw.get('hidden_input_current_page_id') == 'Commercial Registration':
                self.create_commercial_registration_section(kw, client_id, essential_folder_id)
                client_id.sudo().write({'is_commercial_registration': True})
                name = "cr"
                return request.redirect(self.redirect_url(name, client_id))
            elif kw.get('hidden_input_current_page_id') == 'Commercial License':
                self.create_commercial_license_section(kw, client_id, primary_contact, people_folder_id,
                                                       passport_document_type, qid_document_type, essential_folder_id)
                client_id.sudo().write({'is_commercial_license': True})
                name = "cl"
                return request.redirect(self.redirect_url(name, client_id))
            elif kw.get('hidden_input_current_page_id') == 'Establishment Card':
                self.create_establishment_card_section(kw, client_id, essential_folder_id, primary_contact)
                client_id.sudo().write({'is_establishment_card': True})
                name = "ec"
                return request.redirect(self.redirect_url(name, client_id))
            elif kw.get('hidden_input_current_page_id') == 'National Address':
                self.create_national_address_section(kw, client_id)
                client_id.sudo().write({'is_national_address': True})
                name = "na"
                return request.redirect(self.redirect_url(name, client_id))
            elif kw.get('hidden_input_current_page_id') == 'Services':
                if client_id.client_state == 'draft':
                    client_id.client_state = 'under_review'
                self.create_service_section(kw, client_id)
                client_id.sudo().write({'is_form_submit': True, 'is_services_submit': True})
                if client_id.is_summary:
                    return request.redirect('/registration?summary=true')
                elif client_id.is_form_submit:
                    return request.redirect('/registration?submitted=true')
            elif kw.get('hidden_input_current_page_id') == 'Contract Info':
                self.create_contract_info_section(kw, client_id, people_folder_id, passport_document_type,
                                                  qid_document_type)
                client_id.sudo().write({'is_summary': True})
                return request.redirect('/registration?summary=true')
            else:
                request.redirect('/registration')
        except Exception as e:
            client_id.sudo().write({'website_error_msg': e})
            return request.redirect('/registration')

    @http.route(['/contact/delete'], type='json', auth="public", methods=['POST'], website=True)
    def remove_contact_delete(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        contact = request.env['res.partner'].sudo().search([('id', '=', int(kw.get('id')))])
        if kw.get('primary_contact') and contact:
            if contact.id in client_id.contact_child_ids.ids:
                contact_list = client_id.contact_child_ids - contact
                client_id.sudo().write({'contact_child_ids': [(6, 0, contact_list.ids)]})
            if contact.is_newly_create:
                contact.unlink()
            return True
        elif contact and not kw.get('primary_contact'):
            if contact.id in client_id.secondary_contact_child_ids.ids:
                contact_list = client_id.secondary_contact_child_ids - contact
                client_id.sudo().write({'secondary_contact_child_ids': [(6, 0, contact_list.ids)]})
            if contact.is_newly_create:
                contact.unlink()
            return True
        return True

    @http.route(['/contact/update'], type='http', auth="public", csrf=False, methods=['POST'], website=True)
    def update_contact(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        client_record_id = partner_id.client_contact_rel_ids.filtered(
            lambda o: o.client_id.id == client_id.id)
        try:
            if kw.get('contact_id'):
                passport_document_type = request.env['ebs.document.type'].sudo().search(
                    [('meta_data_template', '=', 'Passport')])
                qid_document_type = request.env['ebs.document.type'].sudo().search([('meta_data_template', '=', 'QID')])
                passport_file = kw.get('update_passport_document_extra_contact')
                qid_file = kw.get('update_qid_document_extra_contact')
                contact = request.env['res.partner'].sudo().search([('id', '=', int(kw.get('contact_id')))])
                if contact:
                    # Update Passport Document
                    passport_document = request.env['documents.document'].sudo().search(
                        [('partner_id', '=', contact.id),
                         ('document_type_id', '=',
                          passport_document_type.id)],
                        limit=1)
                    if kw.get('update_qid_radio') == 'no':
                        if passport_file:
                            passport_attachment_id = self.create_passport_qid_document(contact, passport_file)
                            passport_document.sudo().write(
                                {'attachment_id': passport_attachment_id.id})
                        if passport_document:
                            passport_document.sudo().write({
                                'document_number': kw.get('update_passport_extra_contact') or False,
                                'document_type_id': passport_document_type.id,
                                'passport_no': kw.get('update_passport_extra_contact') or False,
                                'gender': kw.get('update_gender_extra_contact') or False,
                                'arabic_name': kw.get('update_passport_name_ar_extra_contact') or False,
                                'passport_name': kw.get('update_passport_name_extra_contact') or False,
                                'passport_type': kw.get('update_passport_type_extra_contact') or False,
                                'expiry_date': parse(kw.get('update_expiry_date_extra_contact')) if kw.get(
                                    'update_expiry_date_extra_contact') else False,
                                'issue_date': parse(kw.get('update_date_of_issue_extra_contact')) if kw.get(
                                    'update_date_of_issue_extra_contact') else False,
                                'date_of_birth': parse(kw.get('update_birth_date_extra_contact')) if kw.get(
                                    'update_birth_date_extra_contact') else False,
                                'place_of_birth': kw.get('update_birth_place_extra_contact') or False,
                                'country_passport_id': int(kw.get('update_nationality_extra_contact')) if kw.get(
                                    'update_nationality_extra_contact') else False,
                            })
                    # Update QID document
                    qid_document = request.env['documents.document'].sudo().search([('partner_id', '=', contact.id),
                                                                                    ('document_type_id', '=',
                                                                                     qid_document_type.id)], limit=1)
                    if kw.get('update_qid_radio') == 'yes':
                        if qid_file:
                            qid_attachment_id = self.create_passport_qid_document(contact, qid_file)
                            qid_document.sudo().write({'attachment_id': qid_attachment_id.id})
                        if qid_document:
                            qid_document.sudo().write({
                                'document_number': kw.get('update_qid_extra_contact') or False,
                                'document_type_id': qid_document_type.id,
                                'arabic_name': kw.get('update_name_ar_extra_contact') or False,
                                'job_title': int(kw.get('update_job_position_extra_contact')) if kw.get(
                                    'update_job_position_extra_contact') else False,
                                'qid_name': kw.get('update_name_english_extra_contact') or False,
                                'expiry_date': parse(kw.get('update_qid_expiry_date_extra_contact')) if kw.get(
                                    'update_qid_expiry_date_extra_contact') else False,
                                'date_of_birth': parse(kw.get('update_qid_birth_date_extra_contact')) if kw.get(
                                    'update_qid_birth_date_extra_contact') else False,
                                'residency_type': kw.get('update_residency_type_extra_contact') or False,
                                'country_passport_id': int(kw.get('update_qid_nationality_extra_contact')) if kw.get(
                                    'update_qid_nationality_extra_contact') else False,
                            })
                    # Update Contact Fields
                    values = {
                        'email': kw.get('update_email_extra_contact') or False,
                        'permission': kw.get('update_extra_contact_permission') or False
                    }
                    update_contact_vals = {
                        'name': kw.get('update_full_name_extra_contact').upper() or False,
                        'mobile': kw.get('update_phone_extra_contact') or False,
                        'email': kw.get('update_email_extra_contact') or False,
                        'arabic_name': kw.get('update_passport_name_ar_extra_contact') or False,
                        'permission': kw.get('update_extra_contact_permission') or False,
                        'qid_resident': True if kw.get('update_qid_radio') == 'yes' else False,
                    }
                    if client_record_id:
                        update_contact_vals.update({
                            'client_contact_rel_ids': [(1, client_record_id.id, values)]
                        })

                    if kw.get('update_qid_radio') == 'yes':
                        update_contact_vals.update({
                            'qid_occupation': int(kw.get('update_job_position_extra_contact')) if kw.get(
                                'update_job_position_extra_contact') else False,
                            'qid_expiry_date': kw.get('update_qid_expiry_date_extra_contact') if kw.get(
                                'update_qid_expiry_date_extra_contact') else False,
                            'qid_ref_no': kw.get('update_qid_extra_contact') or False,
                            'qid_residency_type': kw.get('update_residency_type_extra_contact') or False,
                            'qid_birth_date': parse(kw.get('update_qid_birth_date_extra_contact')) if kw.get(
                                'update_qid_birth_date_extra_contact') else False,
                            'qid_resident': True
                        })
                    elif kw.get('update_qid_radio') == 'no':
                        update_contact_vals.update({
                            'ps_passport_ref_no': kw.get('update_passport_extra_contact') or False,
                            'ps_first_name': kw.get('update_passport_name_extra_contact') or False,
                            'ps_expiry_date': parse(kw.get('update_expiry_date_extra_contact')) if kw.get(
                                'update_expiry_date_extra_contact') else False,
                            'ps_passport_type': kw.get('update_passport_type_extra_contact') or False,
                            'ps_country_passport_id': int(kw.get('update_nationality_extra_contact')) if kw.get(
                                'update_nationality_extra_contact') else False,
                            'ps_birth_date': parse(kw.get('update_birth_date_extra_contact')) if kw.get(
                                'update_birth_date_extra_contact') else False,
                            'ps_gender': kw.get('update_gender_extra_contact') or False,
                            'qid_resident': False,
                        })
                    contact.with_context({'parent_id': client_id.id}).sudo().write(update_contact_vals)
                return json.dumps({})
        except Exception as e:
            client_id.sudo().write({'website_error_msg': e})
            return json.dumps({'error': True})

    @http.route(['/partner/remove'], type='json', auth="public", methods=['POST'], website=True)
    def remove_partner(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        partner = request.env['res.partner'].sudo().search([('id', '=', int(kw.get('id')))])
        if partner:
            commercial_registration_document = client_id.cr_document_id
            if commercial_registration_document:
                partner.sudo().write({'last_client_id': False})
                commercial_registration_document.sudo().write({'cr_partner_ids': [(3, partner.id)]})
            if partner.is_newly_create:
                partner.unlink()

    @http.route(['/authorizer/remove'], type='json', auth="public", methods=['POST'], website=True)
    def remove_authorizer(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        authorizer = request.env['res.partner'].sudo().search([('id', '=', int(kw.get('id')))])
        if authorizer:
            establishment_card_document = client_id.ec_document_id
            if establishment_card_document:
                authorizer.sudo().write({'last_client_id': False})
                establishment_card_document.sudo().write({'cr_authorizers_ids': [(3, authorizer.id)]})
            if authorizer.is_newly_create:
                authorizer.unlink()

    @http.route(['/create_new_contact_person'], type='http', auth="public", methods=['POST'], csrf=False, website=True)
    def create_new_contact_person(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        try:
            commercial_registration_document = client_id.cr_document_id
            establishment_card_document = client_id.ec_document_id

            passport_document_type = request.env['ebs.document.type'].sudo().search(
                [('meta_data_template', '=', 'Passport')])
            if not passport_document_type:
                raise UserWarning("Passport document type has not been configured")
            qid_document_type = request.env['ebs.document.type'].sudo().search([('meta_data_template', '=', 'QID')])
            if not qid_document_type:
                raise UserWarning('QID document type has not been configured')
            people_folder_id = request.env['documents.folder'].sudo().search([('name', 'ilike', 'People')])
            essential_folder_id = request.env['documents.folder'].sudo().search([('name', 'ilike', 'Essential')])
            if not people_folder_id:
                people_folder_id = request.env['documents.folder'].sudo().create({'name': 'People'})
            if not essential_folder_id:
                company_folder_id = request.env['documents.folder'].sudo().create({'name': 'Company'})
                corporate_folder_id = request.env['documents.folder'].sudo().create({
                    'name': 'Corporate Documents',
                    'parent_folder_id': company_folder_id.id,
                })
                essential_folder_id = request.env['documents.folder'].sudo().create({
                    'name': 'Essential',
                    'parent_folder_id': corporate_folder_id.id,
                })
            passport_file = kw.get('passport_document_extra_contact')
            qid_file = kw.get('qid_document_extra_contact')

            if kw.get('form_name') == 'partner' or kw.get('form_name') == 'manager' or kw.get(
                    'form_name') == 'authorizer':
                create_vals_partner_manager = {
                    'name': kw.get('full_name_extra_contact').upper() or False,
                    'mobile': kw.get('phone_extra_contact') or False,
                    'arabic_name': kw.get('full_name_ar_extra_contact') or False,
                    'email': kw.get('email_extra_contact') or False,
                    'permission': kw.get('extra_contact_permission') or False,
                    'last_client_id': client_id.id,
                    'is_newly_create': True,
                }
                partner_manager = request.env['res.partner'].sudo().create(create_vals_partner_manager)
                if kw.get('qid_expiry_date_extra_contact'):
                    partner_manager.sudo().write({'qid_expiry_date': parse(kw.get('qid_expiry_date_extra_contact'))})
                partner_manager_vals = {}
                if passport_file and kw.get('qid_radio') == 'no':
                    passport_attachment_id = self.create_passport_qid_document(partner_manager, passport_file)
                    passport_document = request.env['documents.document'].sudo().create({

                        'attachment_id': passport_attachment_id.id,
                        'document_number': kw.get('passport_extra_contact') or False,
                        'folder_ids': [(6, 0, passport_document_type.folder_ids.ids)],
                        'folder_id': people_folder_id.id,
                        'document_type_id': passport_document_type.id,
                        'partner_id': partner_manager.id,
                        'passport_no': kw.get('passport_extra_contact') or False,
                        'gender': kw.get('gender_extra_contact') or False,
                        'arabic_name': kw.get('passport_name_ar_extra_contact') or False,
                        'passport_name': kw.get('passport_name_extra_contact') or False,
                        'passport_type': kw.get('passport_type_extra_contact') or False,
                        'expiry_date': datetime.strptime(kw['expiry_date_extra_contact'], '%d/%m/%Y') if kw[
                            'expiry_date_extra_contact'] else None,
                        'issue_date': datetime.strptime(kw['date_of_issue_extra_contact'], '%d/%m/%Y') if kw[
                            'date_of_issue_extra_contact'] else None,
                        'date_of_birth': datetime.strptime(kw['birth_date_extra_contact'], '%d/%m/%Y') if kw[
                            'birth_date_extra_contact'] else None,
                        'country_passport_id': int(kw.get('nationality_extra_contact')) if kw.get(
                            'nationality_extra_contact') else False,
                    })
                    partner_manager_vals.update({'ps_passport_serial_no_id': passport_document.id})

                if qid_file and kw.get('qid_radio') == 'yes':
                    qid_attachment_id = self.create_passport_qid_document(partner_manager, qid_file)
                    qid_document = request.env['documents.document'].sudo().create({

                        'attachment_id': qid_attachment_id.id,
                        'document_number': kw.get('qid_extra_contact') or False,
                        'folder_ids': [(6, 0, qid_document_type.folder_ids.ids)],
                        'folder_id': people_folder_id.id,
                        'document_type_id': qid_document_type.id,
                        'partner_id': partner_manager.id,
                        'arabic_name': kw.get('name_ar_extra_contact') or False,
                        'job_title': kw.get('job_position_extra_contact') if kw.get(
                            'job_position_extra_contact') else False,
                        'qid_name': kw.get('name_english_extra_contact') or False,
                        'expiry_date': datetime.strptime(kw['qid_expiry_date_extra_contact'], '%d/%m/%Y') if kw[
                            'qid_expiry_date_extra_contact'] else None,
                        'date_of_birth': datetime.strptime(kw['qid_birth_date_extra_contact'], '%d/%m/%Y') if kw[
                            'qid_birth_date_extra_contact'] else None,
                        'residency_type': kw.get('residency_type_extra_contact') or False,
                        'country_passport_id': int(kw.get('qid_nationality_extra_contact')) if kw.get(
                            'qid_nationality_extra_contact') else False,
                    })
                    partner_manager_vals.update({'qid_residency_id': qid_document.id, 'qid_resident': True})
                partner_manager.sudo().write(partner_manager_vals)
                if kw.get('form_name') == 'partner':
                    return json.dumps(
                        {'id': partner_manager.id,
                         'name': partner_manager.name,
                         'email': partner_manager.email,
                         'mobile': partner_manager.mobile,
                         'ps_passport_ref_no': partner_manager.ps_passport_ref_no,
                         'qid_ref_no': partner_manager.qid_ref_no,
                         'permission': partner_manager.permission,
                         'qid_resident': partner_manager.qid_resident,
                         'form_name': kw.get('form_name'),
                         })
                if kw.get('form_name') == 'manager':
                    return json.dumps(
                        {'id': partner_manager.id,
                         'name': partner_manager.name,
                         'email': partner_manager.email,
                         'mobile': partner_manager.mobile,
                         'ps_passport_ref_no': partner_manager.ps_passport_ref_no,
                         'qid_ref_no': partner_manager.qid_ref_no,
                         'permission': partner_manager.permission,
                         'qid_resident': partner_manager.qid_resident,
                         'form_name': kw.get('form_name'),
                         })
                if kw.get('form_name') == 'authorizer':
                    return json.dumps(
                        {'id': partner_manager.id,
                         'name': partner_manager.name,
                         'email': partner_manager.email,
                         'mobile': partner_manager.mobile,
                         'ps_passport_ref_no': partner_manager.ps_passport_ref_no,
                         'qid_ref_no': partner_manager.qid_ref_no,
                         'permission': partner_manager.permission,
                         'qid_resident': partner_manager.qid_resident,
                         'form_name': kw.get('form_name'),
                         })

            if kw.get('form_name') == 'person' or kw.get('form_name') == 'primary_person':
                create_vals_secondary_contact = {
                    'name': kw.get('full_name_extra_contact').upper() or False,
                    'mobile': kw.get('phone_extra_contact') or False,
                    'email': kw.get('email_extra_contact') or False,
                    'permission': kw.get('extra_contact_permission') or False,
                    'is_newly_create': True,
                    'arabic_name': kw.get('full_name_ar_extra_contact') or False,
                }

                secondary_contact = request.env['res.partner'].sudo().create(create_vals_secondary_contact)

                secondary_contact_vals = {}
                if passport_file and kw.get('qid_radio') == 'no':
                    passport_attachment_id = self.create_passport_qid_document(secondary_contact, passport_file)
                    passport_document = request.env['documents.document'].sudo().create({

                        'attachment_id': passport_attachment_id.id,
                        'document_number': kw.get('passport_extra_contact') or False,
                        'folder_ids': [(6, 0, passport_document_type.folder_ids.ids)],
                        'folder_id': people_folder_id.id,
                        'document_type_id': passport_document_type.id,
                        'partner_id': secondary_contact.id,
                        'passport_no': kw.get('passport_extra_contact') or False,
                        'gender': kw.get('gender_extra_contact') or False,
                        'arabic_name': kw.get('passport_name_ar_extra_contact') or False,
                        'passport_name': kw.get('passport_name_extra_contact') or False,
                        'passport_type': kw.get('passport_type_extra_contact') or False,
                        'expiry_date': datetime.strptime(kw['expiry_date_extra_contact'], '%d/%m/%Y') if kw[
                            'expiry_date_extra_contact'] else None,
                        'issue_date': datetime.strptime(kw['date_of_issue_extra_contact'], '%d/%m/%Y') if kw[
                            'date_of_issue_extra_contact'] else None,
                        'date_of_birth': datetime.strptime(kw['birth_date_extra_contact'], '%d/%m/%Y') if kw[
                            'birth_date_extra_contact'] else None,
                        'country_passport_id': int(kw.get('nationality_extra_contact')) if kw.get(
                            'nationality_extra_contact') else False,
                    })
                    secondary_contact_vals.update({'ps_passport_serial_no_id': passport_document.id})

                if qid_file and kw.get('qid_radio') == 'yes':
                    qid_attachment_id = self.create_passport_qid_document(secondary_contact, qid_file)
                    qid_document = request.env['documents.document'].sudo().create({

                        'attachment_id': qid_attachment_id.id,
                        'document_number': kw.get('qid_extra_contact') or False,
                        'folder_ids': [(6, 0, qid_document_type.folder_ids.ids)],
                        'folder_id': people_folder_id.id,
                        'document_type_id': qid_document_type.id,
                        'partner_id': secondary_contact.id,
                        'arabic_name': kw.get('name_ar_extra_contact') or False,
                        'job_title': int(kw.get('job_position_extra_contact')) if kw.get(
                            'job_position_extra_contact') else False,
                        'qid_name': kw.get('name_english_extra_contact') or False,
                        'expiry_date': parse(kw['qid_expiry_date_extra_contact']) if kw[
                            'qid_expiry_date_extra_contact'] else None,
                        'date_of_birth': parse(kw['qid_birth_date_extra_contact']) if kw[
                            'qid_birth_date_extra_contact'] else None,
                        'residency_type': kw.get('residency_type_extra_contact') or False,
                        'country_passport_id': int(kw.get('qid_nationality_extra_contact')) if kw.get(
                            'qid_nationality_extra_contact') else False,
                    })
                    secondary_contact_vals.update({'qid_residency_id': qid_document.id, 'qid_resident': True})

                secondary_contact.sudo().write(secondary_contact_vals)
                email_permission_vals = secondary_contact.get_client_contact_rel_vals(client_id)
                return json.dumps({'id': secondary_contact.id,
                                   'name': secondary_contact.name,
                                   'email': secondary_contact.email,
                                   'mobile': secondary_contact.mobile,
                                   'ps_passport_ref_no': secondary_contact.ps_passport_ref_no,
                                   'qid_ref_no': secondary_contact.qid_ref_no,
                                   'permission': secondary_contact.permission,
                                   'form_name': kw.get('form_name'),
                                   'qid_resident': secondary_contact.qid_resident
                                   })
        except Exception as e:
            client_id.sudo().write({'website_error_msg': e})
            return json.dumps({'error': True})

    # Todo: Remove in future, handled by adding id of contact to js list

    @http.route(['/manager/remove'], type='json', auth="public", methods=['POST'], website=True)
    def manager_remove(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        manager = request.env['res.partner'].sudo().search([('id', '=', int(kw.get('id')))])
        if manager:
            commercial_registration_document = client_id.cr_document_id
            if commercial_registration_document:
                manager.sudo().write({'last_client_id': False})
                commercial_registration_document.sudo().write({'cr_managers_ids': [(3, manager.id)]})
            if manager.is_newly_create:
                manager.unlink()

    @http.route(['/create_new_activity'], type='json', auth="public", methods=['POST'], website=True)
    def create_new_activitty(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        commercial_registration_document = client_id.cr_document_id
        business_activtie = request.env['business.activities'].sudo().search([('name', '=', kw.get('activity_name'))],
                                                                             limit=1)
        if not business_activtie:
            business_activtie = request.env['business.activities'].sudo().create({
                'name': kw.get('activity_name')
            })
            commercial_registration_document.sudo().write({'cr_business_activities_ids': [(4, business_activtie.id)]})
            return {
                'activity_name': business_activtie.name,
                'activity_id': business_activtie.id,
            }

    @http.route(['/activity/update'], type='json', auth="public", methods=['POST'], website=True)
    def update_activity(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        commercial_registration_document = client_id.cr_document_id
        if kw.get('old_activity_id') and kw.get('new_activity_id') and commercial_registration_document:
            commercial_registration_document.sudo().write(
                {'cr_business_activities_ids': [(3, int(kw.get('old_activity_id'))),
                                                (
                                                    4, int(kw.get('new_activity_id')))]})
            return json.dumps({})

    @http.route(['/activity/remove'], type='json', auth="public", methods=['POST'], website=True)
    def activity_remove(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        commercial_registration_document = client_id.cr_document_id
        if int(kw.get('id')) and commercial_registration_document:
            commercial_registration_document.sudo().write({'cr_business_activities_ids': [(3, int(kw.get('id')))]})
            print("return success")
            return json.dumps({'msg': 'success'})
        print("return error")
        return json.dumps({'msg': 'error'})

    @http.route(['/activity_exist/create'], type='json', auth="public", methods=['POST'], website=True)
    def create_exist_activity(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        commercial_registration_document = client_id.cr_document_id
        if kw.get('id') and commercial_registration_document:
            if int(kw.get('id')) not in commercial_registration_document.cr_business_activities_ids.ids:
                commercial_registration_document.sudo().write({'cr_business_activities_ids': [(4, int(kw.get('id')))]})
                return json.dumps({'msg': 'success'})
        return json.dumps({'msg': 'error'})

    @http.route(['/activity/search'], type='json', auth="public", methods=['POST'], website=True)
    def search_activity(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        domain = []
        commercial_registration_document = client_id.cr_document_id
        if kw.get('activity_name') and commercial_registration_document.cr_partner_ids:
            domain.append(('id', 'not in', commercial_registration_document.cr_business_activities_ids.ids))
        if kw.get('activity_name') != '':
            domain.append(('name', '=', kw.get('activity_name')))
        if domain:
            activity = request.env['business.activities'].sudo().search(domain, limit=1)
            if activity:
                return {
                    'name': activity.name,
                    'id': activity.id,
                }
            return False
        return False

    @http.route(['/render/report'], type='json', auth="public", website=True)
    def render_report(self, **kw):
        if kw.get('id'):
            client_contract = request.env['ebs.crm.proposal'].sudo().search([('id', '=', int(kw.get('id')))])
            pdf = request.env.ref('ebs_fusion_services.services_agreement_report_template_action').render_qweb_pdf(
                [client_contract.id])
            b64_pdf = base64.b64encode(pdf[0])
            return {
                'pdf_data': b64_pdf
            }
        else:
            return False

    def send_email(self, client):
        """ send notification email to a new portal user """

        # determine subject and body in the portal user's language
        template = request.env.ref('portal.mail_template_data_portal_welcome')
        for wizard_line in self:
            lang = wizard_line.user_id.lang
            partner = wizard_line.user_id.partner_id
            portal_url = partner.with_context(signup_force_type_in_url='', lang=lang)._get_signup_url_for_action()[
                partner.id]
            partner.signup_prepare()
            if template:
                template.with_context(dbname=self._cr.dbname, portal_url=portal_url, lang=lang).send_mail(
                    wizard_line.id, force_send=True)
        return True

    def return_json_value(self, partner, client_id):
        contact_list = []
        print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz", partner)
        for rec in partner:
            email_permission_vals = rec.get_client_contact_rel_vals(client_id)
            main_email = ""
            main_permission = ""
            if email_permission_vals.get('email'):
                main_email = email_permission_vals.get('email')
            else:
                main_email = rec.email
            if email_permission_vals.get('permission'):
                main_permission = email_permission_vals.get('permission')
            else:
                main_permission = rec.permission
            contact_list.append({
                'ps_passport_ref_no': rec.ps_passport_ref_no,
                'qid_ref_no': rec.qid_ref_no,
                'permission': main_permission,
                'name': rec.name,
                'mobile': rec.mobile,
                'email': main_email,
                'id': rec.id,
            })

        return {
            'contact_list': contact_list,
        }

    @http.route(['/search/partner/manager/person'], type='json', auth="public", methods=['POST'], website=True)
    def search_data_of_modal_partner_manager_person(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        establishment_card_document = client_id.ec_document_id
        commercial_registration_document = client_id.cr_document_id
        contact_ = False
        if kw.get('document_id'):
            contact_ = request.env['res.partner'].sudo().search(
                ['&', ('is_company', '!=', True), '|',
                 ('name', 'ilike', kw.get('document_id')), '|',
                 ('ps_passport_ref_no', '=', kw.get('document_id')),
                 ('qid_ref_no', '=', kw.get('document_id'))])
        if kw.get('who_call') == "person" or kw.get('who_call') == "primary_person":
            if kw.get('document_id'):
                secondary_contact_ids = contact_ - client_id.secondary_contact_child_ids
                contact_ids = secondary_contact_ids - client_id.contact_child_ids
                if contact_ids:
                    return self.return_json_value(contact_ids, client_id)
                return False
            return False
        elif kw.get('who_call') == "partner":
            if kw.get('document_id'):
                partner_lst = []
                for rec in contact_:
                    if rec.id not in commercial_registration_document.cr_partner_ids.ids:
                        if rec.client_contact_rel_ids:
                            search_partner = rec.client_contact_rel_ids.filtered(
                                lambda reco: reco.client_id.id == client_id.id and reco.is_shareholder == True)
                            if not search_partner:
                                partner_lst.append(rec)
                        else:
                            partner_lst.append(rec)
                if partner_lst:
                    return self.return_json_value(partner_lst, client_id)
                return False
            return False
        elif kw.get('who_call') == "manager":
            if kw.get('document_id'):
                manager_lst = []
                for rec in contact_:
                    if rec.id not in commercial_registration_document.cr_managers_ids.ids:
                        if rec.client_contact_rel_ids:
                            search_partner = rec.client_contact_rel_ids.filtered(
                                lambda reco: reco.client_id.id == client_id.id and reco.is_manager_cr == True)
                            if not search_partner:
                                manager_lst.append(rec)
                        else:
                            manager_lst.append(rec)
                if manager_lst:
                    return self.return_json_value(manager_lst, client_id)
                return False
            return False
        elif kw.get('who_call') == "authorizer":
            if kw.get('document_id'):
                authorizer_lst = []
                for rec in contact_:
                    if rec.id not in establishment_card_document.cr_authorizers_ids.ids:
                        if rec.client_contact_rel_ids:
                            search_partner = rec.client_contact_rel_ids.filtered(
                                lambda reco: reco.client_id.id == client_id.id and reco.is_manager_ec == True)
                            if not search_partner:
                                authorizer_lst.append(rec)
                        else:
                            authorizer_lst.append(rec)
                if authorizer_lst:
                    return self.return_json_value(authorizer_lst, client_id)
                return False
            return False

    @http.route(['/grant_portal_access'], type='json', auth="public", methods=['POST'], website=True)
    def grant_portal_access(self, **kw):
        contact_ids = set()
        wiz_record = request.env['portal.wizard'].sudo().create({
            'welcome_message': 'welcome'
        })
        if kw.get('id'):
            for partner in request.env['res.partner'].sudo().browse(int(kw.get('id'))):
                if partner:
                    if partner.email:
                        unique_partner = request.env['res.partner'].sudo().search([('email', '=', partner.email)])
                        if not len(unique_partner) > 1:
                            contact_partners = partner.child_ids.filtered(
                                lambda p: p.type in ('contact', 'other')) | partner
                            for contact in contact_partners:
                                # make sure that each contact appears at most once in the list
                                if contact.id not in contact_ids:
                                    contact_ids.add(contact.id)
                                    in_portal = True
                                    if contact.user_ids:
                                        in_portal = request.env.ref('base.group_portal') in contact.user_ids[
                                            0].groups_id
                                    wiz_record_user = request.env['portal.wizard.user'].sudo().create({
                                        'partner_id': contact.id,
                                        'email': contact.email,
                                        'in_portal': in_portal,
                                        'wizard_id': wiz_record.id
                                    })
                            wiz_record.action_apply()
                            return {'success_message': 'Your portal invitation URL is given in your mail inbox.'}
                        return {
                            'error_message': 'Some contacts have the same email as an existing portal user. Correct the email of the relevant contacts!'}
                return {'error_message': ' There is no a record found please please try again!'}
        else:
            return {'error_message': ' Something went wrong please try again!'}

    @http.route(['/attachment/contract_download'], type='http', auth='public')
    def download_contract_attachment(self, contract_id):
        client_contract = request.env['ebs.crm.proposal'].sudo().search([('id', '=', contract_id)])
        attachment_id = request.env['ir.attachment'].sudo().search([('res_model', '=', 'ebs.crm.proposal'),
                                                                    ('res_id', '=', client_contract.id)])

        if not attachment_id:
            pdf = request.env.ref('ebs_fusion_services.services_agreement_report_template_action').render_qweb_pdf(
                [client_contract.id])
            b64_pdf = base64.b64encode(pdf[0])
            data = BytesIO(base64.standard_b64decode(b64_pdf))
            if b64_pdf:
                attachment_id = request.env['ir.attachment'].sudo().create({
                    'name': client_contract.contract_no + '.pdf',
                    'type': 'binary',
                    'datas': b64_pdf,
                    'res_model': 'ebs.crm.proposal',
                    'public': True,
                    'res_id': client_contract.id,
                    'mimetype': 'application/pdf'
                })
                attachment_id = attachment_id[0]
                return http.send_file(BytesIO(base64.standard_b64decode(attachment_id['datas'])),
                                      filename=attachment_id['name'], as_attachment=True)
            else:
                return request.not_found()
        else:
            attachment_id = attachment_id[0]
            return http.send_file(BytesIO(base64.standard_b64decode(attachment_id['datas'])),
                                  filename=attachment_id['name'], as_attachment=True)

    @http.route(['/edit/search_id'], type='json', auth="public", methods=['POST'], website=True)
    def edit_search_contact(self, **kw):
        partner_id = request.env.user.partner_id
        if not partner_id.last_client_id and partner_id.client_contact_rel_ids:
            partner_id.sudo().write({'last_client_id': partner_id.client_contact_rel_ids[0].client_id.id})
        client_id = partner_id.last_client_id
        passport_document_type = request.env['ebs.document.type'].sudo().search(
            [('meta_data_template', '=', 'Passport')])
        qid_document_type = request.env['ebs.document.type'].sudo().search([('meta_data_template', '=', 'QID')])
        contact = request.env['res.partner'].browse(int(kw.get('id')))

        if contact:
            passport_document = request.env['documents.document'].sudo().search(
                [('partner_id', '=', contact.id), ('partner_id', '!=', False),
                 ('document_type_id', '=', passport_document_type.id)])
            qid_document = request.env['documents.document'].sudo().search(
                [('partner_id', '=', contact.id), ('partner_id', '!=', False),
                 ('document_type_id', '=', qid_document_type.id)])
            email_permission_vals = contact.get_client_contact_rel_vals(client_id)
            main_email = ""
            main_permission = ""
            if email_permission_vals.get('email'):
                main_email = email_permission_vals.get('email')
            else:
                main_email = contact.email
            if email_permission_vals.get('permission'):
                main_permission = email_permission_vals.get('permission')
            else:
                main_permission = contact.permission
            return {
                'en_name': contact.name if contact.name else '',
                'email': main_email,
                'qid_attachment_id': qid_document.attachment_id.id,
                'passport_attachment_id': passport_document.attachment_id.id,
                'qid_document_name': qid_document.name,
                'passport_attachment_name': passport_document.name,
                'mobile': contact.mobile if contact.mobile else '',
                'ar_name': contact.arabic_name if contact.arabic_name else '',
                'ps_passport_ref_no': contact.ps_passport_ref_no if contact.ps_passport_ref_no else '',
                'ps_qid_no': contact.qid_ref_no if contact.qid_ref_no else '',
                'permission': main_permission,
                'ps_birth_date': contact.ps_birth_date if contact.ps_birth_date else '',
                'qid_birth_date': contact.qid_birth_date if contact.qid_birth_date else '',
                'qid_resident': contact.qid_resident,
                'gender': contact.ps_gender if contact.ps_gender else '',
                'passport_type': contact.ps_passport_type if contact.ps_passport_type else '',
                'passport_issue_date': contact.ps_issue_date if contact.ps_issue_date else '',
                'passport_country': contact.ps_country_passport_id.id if contact.ps_country_passport_id.id else '',
                'qid_country': qid_document.country_passport_id.id if qid_document.country_passport_id.id else '',
                'passport_expiry_date': contact.ps_expiry_date if contact.ps_expiry_date else '',
                'qid_expiry_date': contact.qid_expiry_date if contact.qid_expiry_date else '',
                'job_position': contact.qid_occupation.id if contact.qid_occupation else '',
                'residency_type': qid_document.residency_type if qid_document.residency_type else '',
            }

    @http.route(['/invoices'], type='http', auth="public", website=True)
    def portal_invoices_menu(self, **kw):
        return request.render("ebs_fusion_theme.portal_invoices_menu")

    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content',
                           **kw):
        values = self._prepare_portal_layout_values()
        AccountInvoice = request.env['account.move']
        partner = request.env.user.partner_id

        if not partner.last_client_id and partner.client_contact_rel_ids:
            partner.sudo().write({'last_client_id': partner.client_contact_rel_ids[0].client_id.id})
        domain = [
            ('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')),
            ('partner_id', '=', partner.last_client_id.id), ('state', '!=', 'draft')]
        if kw.get('state'):
            domain.append(('state', '=', kw.get('state')))
            domain.append(('payment_state', '!=', 'paid'))
        if kw.get('payment_state'):
            domain.append(('payment_state', '=', kw.get('payment_state')))
        searchbar_sortings = {
            'date': {'label': _('Invoice Date'), 'order': 'invoice_date desc'},
            'duedate': {'label': _('Due Date'), 'order': 'invoice_date_due desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }

        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Name'), 'type': 'text'},
            'invoice_date': {'input': 'invoice_date', 'label': _('Date'), 'type': 'date'},
            'status': {'input': 'status', 'label': _('Status'), 'type': 'text'},
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>'),
                        'type': 'text'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        if search and search_in:
            search_domain = []
            if search_in == 'state':
                search_domain = OR([search_domain, [('state', 'ilike', search)]])
            if search_in == 'name':
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in == 'invoice_date':
                search_domain = OR([search_domain, [('invoice_date', 'ilike', search)]])
            if search_in == 'status':
                search_domain = OR([search_domain, [('state', 'ilike', search)]])
            if search_in == 'content':
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('state', 'ilike', search)]])
            domain += search_domain
        # count for pager
        invoice_count = AccountInvoice.sudo().search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/invoices",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby,
                      'payment_state': kw.get('payment_state'), 'state': kw.get('state'), },
            total=invoice_count,
            page=page,
            step=10
        )
        # content according to pager and archive selected
        invoices = AccountInvoice.sudo().search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_invoices_history'] = invoices.ids[:100]
        employee_ids = request.env['hr.employee'].sudo().search([])
        all_services = request.env['ebs.crm.service'].sudo().search([], order='category_id')
        nationalities = request.env['res.country'].sudo().search([])
        job_positions = request.env['hr.job'].sudo().search([])
        related_clients = request.env['ebs.client.contact'].sudo().search([('partner_id', '=', partner.id)]).mapped(
            'client_id')
        client_contracts = request.env['ebs.crm.proposal'].sudo().search(
            [('contact_id', '=', partner.last_client_id.id), ('type', '=', 'proposal')])
        client_employee_ids = request.env['hr.employee'].sudo().search(
            [('partner_parent_id', '=', partner.last_client_id.id)])

        values.update({
            'date': date_begin,
            'invoices': invoices,
            'page_name': 'invoice',
            'related_clients': related_clients,
            'pager': pager,
            'last_client_id': partner.last_client_id.id,
            'default_url': '/my/invoices',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search': search,
            'search_in': search_in,
            'employee_ids': employee_ids,
            'all_services': all_services,
            'client_employee_ids': client_employee_ids,
            'nationalities': nationalities,
            'job_positions': job_positions,
            'client_contracts': client_contracts,
        })
        return request.render("account.portal_my_invoices", values)

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="user", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=invoice_sudo, report_type=report_type, report_ref='account.account_invoices',
                                     download=download)
        partner = request.env.user.partner_id

        if not partner.last_client_id and partner.client_contact_rel_ids:
            partner.sudo().write({'last_client_id': partner.client_contact_rel_ids[0].client_id.id})
        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        related_clients = request.env['ebs.client.contact'].sudo().search([('partner_id', '=', partner.id)]).mapped(
            'client_id')
        client_contracts = request.env['ebs.crm.proposal'].sudo().search(
            [('contact_id', '=', partner.last_client_id.id), ('type', '=', 'proposal')])
        values.update({
            'client_contracts': client_contracts,
            'related_clients': related_clients,
            'last_client_id': partner.last_client_id.id
        })

        acquirers = values.get('acquirers')
        if acquirers:
            country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(invoice_sudo.amount_residual,
                                                                         invoice_sudo.currency_id, country_id)

        return request.render("account.portal_invoice_page", values)

    @http.route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        client_id = request.env.user.partner_id
        if not client_id.last_client_id and client_id.client_contact_rel_ids:
            client_id.sudo().write({'last_client_id': client_id.client_contact_rel_ids[0].client_id.id})
        client = request.env['res.partner'].sudo().browse(client_id.id)
        related_clients = request.env['ebs.client.contact'].sudo().search([('partner_id', '=', client_id.id)]).mapped(
            'client_id')
        client_documents = request.env['documents.document'].sudo().search(
            [('partner_id', '=', client_id.last_client_id.id)])
        client_employees = client_id.last_client_id.client_employee_ids
        outsourced_employees = client_id.last_client_id.fos_employee_ids
        labor_quota_lines = client_id.last_client_id.labor_quota_ids.labor_quota_line_id
        return request.render("ebs_fusion_theme.portal_my_details",
                              {'client': client, 'related_clients': related_clients,
                               'last_client_id': client_id.last_client_id,
                               'documents': client_documents,
                               'client_employees': client_employees,
                               'outsourced_employees': outsourced_employees,
                               'labor_quota_lines': labor_quota_lines, })

    @http.route(['/set/last_client_value'], type='json', auth="public", methods=['POST'], website=True)
    def last_client_value_set(self, **kw):
        partner_id = request.env.user.partner_id
        if kw.get('last_client_value'):
            partner_id.sudo().write({'last_client_id': int(kw.get('last_client_value'))})

    @http.route(['/search/activity'], type='json', auth="public", methods=['POST'], website=True)
    def search_activity(self, **kw):
        if kw.get('name'):
            activity_name_results = request.env['business.activities'].sudo().search(
                [('name', 'ilike', kw.get('name'))], limit=1)
            activity_code_results = request.env['business.activities'].sudo().search(
                [('code', 'ilike', kw.get('name'))], limit=1)
            return {
                'activity_name': activity_name_results.id if activity_name_results else False,
                'activity_code': activity_code_results.id if activity_code_results else False,
            }

    @http.route(['/get/authorizer'], type='json', auth="public", methods=['POST'], website=True)
    def get_authorizer(self, **kw):
        partner_id = request.env.user.partner_id
        client_id = partner_id.last_client_id
        establishment_card_document = client_id.ec_document_id
        commercial_registration_document = client_id.cr_document_id
        if not establishment_card_document:
            cr_authorizers_ids = commercial_registration_document.cr_managers_ids.ids
            return {
                'auth_ids': cr_authorizers_ids
            }
        else:
            return {
                'auth_ids': False
            }

    @http.route(['/set/client_err_msg'], type='json', auth="public", methods=['POST'], website=True)
    def client_err_msg_set(self, **kw):
        partner_id = request.env.user.partner_id
        if kw.get('last_client_value'):
            client_id = request.env['res.partner'].browse(int(kw.get('last_client_value')))
            client_id.sudo().write({'website_error_msg': False})

    @http.route(['/date_name_nationality/checker'], type='json', auth="public", methods=['POST'], website=True)
    def date_name_nationality_checker(self, **kw):
        if kw.get('name') and kw.get('birth_date') and kw.get('nationality'):
            date = datetime.strptime(parse(kw.get('birth_date')).date().strftime('%d/%m/%Y'), '%d/%m/%Y').date()
            duplicate_found = request.env['res.partner'].sudo().search(
                [('name', '=', kw.get('name').upper()), ('dob', '=', date),
                 ('nationality_id', '=', int(kw.get('nationality')))])
            if duplicate_found:
                return True
            else:
                return False

    @http.route(['/check/duplicate_document'], type='json', auth="public", methods=['POST'], website=True)
    def check_duplicate_document(self, **kw):
        partner_document = request.env['documents.document']
        if kw.get('type') == 'Passport':
            partner_document = request.env['res.partner'].browse(
                [(int(kw.get('contact_id')))] if kw.get('contact_id') else []).ps_passport_serial_no_id
        if kw.get('type') == 'QID':
            partner_document = request.env['res.partner'].browse(
                [(int(kw.get('contact_id')))] if kw.get('contact_id') else []).qid_residency_id
        document_id = request.env['documents.document'].sudo().search([('document_type_name', '=', kw.get('type')),
                                                                       ('document_number', '=',
                                                                        kw.get('val'))]) - partner_document
        if document_id:
            return True
        else:
            return False

    @http.route(['/confirm_proforma_invoice'], type='json', auth="public", website=True)
    def confirm_proforma_invoice(self, **kw):
        if kw.get('payment_id'):
            payment_id = request.env['account.payment'].sudo().search(
                [('id', '=', int(kw.get('payment_id')))])
            payment_id.sudo().post()
        return True

    @http.route(['/confirm_appointment'], type='json', auth="public", website=True)
    def confirm_appointment(self, **kw):
        partner_id = request.env.user.partner_id
        client_id = partner_id.last_client_id
        if kw.get('member_id'):
            member_id = request.env['res.users'].sudo().search([('id', '=', int(kw.get('member_id')))])
        else:
            member_id = client_id.client_account_manager_id

        smtp = request.env['ir.mail_server'].sudo().search([('name', '=', 'Info.system')])
        if smtp:
            recipient_ids = [(4, member_id.partner_id.id)]
            subject = 'Appointment Requested'
            body = '<p>%s from %s requested an appointment.</p>' % (partner_id.name, client_id.name)
            mail = request.env['mail.mail'].sudo().create({
                'subject': subject,
                'body_html': body,
                'recipient_ids': recipient_ids,
                'mail_server_id': smtp and smtp.id,
                'email_from': smtp.smtp_user,
            })
            mail.sudo().send()
        return True

    @http.route(['/confirm_invoice'], type='json', auth="public", website=True)
    def confirm_invoice(self, **kw):
        if kw.get('invoice_id'):
            invoice_id = request.env['account.move'].sudo().search(
                [('id', '=', int(kw.get('invoice_id')))])
            payment_journal_id = request.env['account.journal'].sudo().search(
                [('company_id', '=', invoice_id.company_id.id), ('type', 'in', ('bank', 'cash'))], limit=1)
            pmt_wizard = request.env['account.payment.register'].with_context({
                'active_model': 'account.move', 'active_ids': invoice_id.ids
            }).sudo().create({
                'journal_id': payment_journal_id.id,
                'payment_date': datetime.today().date(),
            })
            pmt_wizard.sudo().action_create_payments()
        return True


class Home(Home):

    @http.route()
    def index(self, *args, **kw):
        if request.session.uid and not request.env['res.users'].sudo().browse(request.session.uid).has_group(
                'base.group_user'):
            # return http.local_redirect('/web', query=request.params, keep_hash=True)
            return request.redirect('/web', query=request.params, keep_hash=True)
        return super(Home, self).index(*args, **kw)

    def _login_redirect(self, uid, redirect=None):
        redirect = request.httprequest.url_root + "web"
        if not redirect:
            return '/web'
        return super(Home, self)._login_redirect(uid, redirect=redirect)

    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):

        return super(Home, self).web_client(s_action, **kw)
