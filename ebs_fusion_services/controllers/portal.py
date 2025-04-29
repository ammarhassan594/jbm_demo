import base64
from datetime import date
from io import BytesIO

import werkzeug
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from werkzeug.utils import redirect

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.osv.expression import OR


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        ServiceOrder = request.env['ebs.crm.service.process']
        service_count = ServiceOrder.sudo().search_count([
            ('partner_id', '=', partner.id),

        ])
        values.update({
            'service_count': service_count,
        })
        return values

    @http.route(['/search/pricelist_category'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_pricelist_lines(self, **kw):
        pricelist_id = request.env['ebs.crm.pricelist'].browse([int(kw.get('pricelist_id'))])
        lines = request.env['ebs.crm.pricelist.line'].sudo().search(
            [('show_in_portal', '=', True), ('pricelist_id', '=', pricelist_id.id),
             ('pricelist_category_id', '=', int(kw.get('pricelist_category')))])
        return {
            'lines': [(line.id, line.name) for line in lines],
        }

    @http.route(['/search/company'], type='json', auth="public", methods=['POST'],
                website=True)
    def getpricelist(self, **kw):
        company_id = request.env['res.company'].browse([int(kw.get('company'))])
        domain = [('company_id', '=', company_id.id), ('date_from', '<=', date.today()),
                  ('date_to', '>=', date.today())]
        if kw.get('individual'):
            domain.append(('type', '=', 'individual'))
        else:
            domain.append(('type', '=', 'company'))
        pricelist_id = request.env['ebs.crm.pricelist'].sudo().search(domain, limit=1)
        return {
            'name': pricelist_id.name,
            'id': pricelist_id.id,
        }

    @http.route(['/search/contacts'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_contacts(self, **kw):

        individual = kw.get('individual')
        if individual:
            partners = request.env['res.partner'].sudo().search(
                [('is_company', '!=', True)])
            return {
                'contacts': [(contact.id, contact.name) for contact in partners],
            }

    @http.route(['/get/target_audience_types'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_target_audience_types(self, service, **kw):
        service_id = request.env['ebs.crm.service'].sudo().search([('id', '=', int(service))])
        return {
            'company': service_id.company,
            'employee': service_id.employee,
            'visitor': service_id.visitor,
        }

    @http.route(['/get/company'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_company(self, **kw):
        partner = request.env.user.partner_id
        if partner:
            return {
                'company': [(partner.parent_id.id, partner.parent_id.name)],
            }

    @http.route(['/get/contacts'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_contacts(self, type, **kw):

        if type == 'client':
            partners = request.env['res.partner'].sudo().search(
                ['|', ('company_partner', '=', True), ('is_customer', '=', True), ('is_company', '=', True)])
            return {
                'type': 'client',
                'contacts': [(contact.id, contact.name) for contact in partners],
            }
        if type == 'contact':
            partners = request.env['res.partner'].sudo().search([('is_company', '=', False)])
            return {
                'type': 'contact',
                'contacts': [(contact.id, contact.name) for contact in partners],
            }
        if type == 'dependant':
            partners = request.env['res.partner'].sudo().search([('is_dependent', '=', True)])
            return {
                'type': 'dependant',
                'contacts': [(contact.id, contact.name) for contact in partners],
            }
        if type == 'employee':
            employees = request.env['hr.employee'].sudo().search([])
            return {
                'type': 'employee',
                'contacts': [(contact.id, contact.name) for contact in employees],
            }

    @http.route(['/search/pricelist'], type='json', auth="public", methods=['POST'],
                website=True)
    def getcategories(self, **kw):
        pricelist_id = request.env['ebs.crm.pricelist'].browse([int(kw.get('pricelist'))])
        pricelist_lines = request.env['ebs.crm.pricelist.line'].sudo().search(
            [('show_in_portal', '=', True), ('pricelist_id', '=', pricelist_id.id)])
        pricelist_categories = []
        for line in pricelist_lines:
            pricelist_categories.append(line.pricelist_category_id)
        return {
            'categories': [(category.id, category.name) for category in pricelist_categories],
        }

    @http.route(['/search/pricelistline'], type='json', auth="public", methods=['POST'],
                website=True)
    def getfees(self, **kw):
        pricelist_line_id = request.env['ebs.crm.pricelist.line'].browse([int(kw.get('pricelist_line'))])
        return {
            'fusion': pricelist_line_id.fusion_fees,
            'fusion_urgent': pricelist_line_id.fusion_urgent_fees,
            'govt': pricelist_line_id.govt_fees,
            'govt_urgent': pricelist_line_id.govt_urgent_fees,
            'comments': pricelist_line_id.comments,
            'currency': pricelist_line_id.company_id.currency_id.symbol,
        }

    @http.route(['/search/document_type'], type='json', auth="public", methods=['POST'],
                website=True)
    def document_type(self, **kw):
        document_type_id = request.env['ebs.document.type'].sudo().search([('id', '=', int(kw.get('doc_type_id')))])
        return {
            'required': document_type_id.has_issue_expiry_date,
            'id': document_type_id.id,
            'name': document_type_id.name,
        }

    @http.route(['/search/all/document_type'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_all_document_type(self, **kw):
        document_type_ids = request.env['ebs.document.type'].sudo().search([])
        return {
            'types': [(type.id, type.name) for type in document_type_ids],
        }

    @http.route(['/submit_service_document'], type='http', auth="public", website=True)
    def portal_submit_service_document(self, **post):
        partner = request.env.user.partner_id
        name = post.get('doc_file').filename
        file = post.get('doc_file')
        document_type_id = request.env['ebs.document.type'].sudo().search([('id', '=', int(post.get('doc_type')))])
        service_order = request.env['ebs.crm.service.process'].sudo().search(
            [('id', '=', int(post.get('service_order')))])
        doc_ids = service_order.in_document_ids
        in_document_id = ''
        for doc in doc_ids:
            if document_type_id.id == doc.doc_type_id.id:
                in_document_id = doc
        Attachments = request.env['ir.attachment']
        attachment_id = Attachments.sudo().create({
            'name': name,
            'type': 'binary',
            'datas': base64.b64encode(file.read()),
        })
        document_type_id = request.env['ebs.document.type'].sudo().search([('id', '=', int(post.get('doc_type')))])
        if document_type_id.folder_id:
            folder_id = document_type_id.folder_id
        else:
            folder_id = request.env['documents.folder'].sudo().search([('is_default_folder', '=', True)], limit=1)
        mimetype = self._neuter_mimetype(file.content_type, http.request.env.user)
        document_vals = {
            'name': name,
            'mimetype': mimetype,
            'folder_id': int(folder_id.id),
            'partner_id': int(partner.id),
            'attachment_id': attachment_id.id,
            'document_type_id': int(post.get('doc_type')),
            'owner_id': request.env.user.id,
            'document_number': post.get('document_number'),
            'res_model': partner._name,
            'res_id': partner.id
        }
        if post.get('issue_date'):
            document_vals.update({'issue_date': post.get('issue_date')})
        if post.get('expiry_date'):
            document_vals.update({'expiry_date': post.get('expiry_date')})
        document_id = request.env['documents.document'].sudo().create(document_vals)
        attachment_id.sudo().write({'res_id': document_id.id})
        if in_document_id:
            in_document_id.sudo().write({'name': document_id.id})
        return werkzeug.utils.redirect('/my/docs/%s' % (document_id.id))

    @http.route(['/attachment/download'], type='http', auth='public')
    def download_attachment(self, attachment_id):
        # Check if this is a valid attachment id
        attachment = request.env['ir.attachment'].sudo().search_read(
            [('id', '=', int(attachment_id))],
            ["name", "datas", "res_model", "res_id", "type", "url"]
        )
        if attachment:
            attachment = attachment[0]
        else:
            return redirect('/event')

        if attachment["type"] == "url":
            if attachment["url"]:
                return redirect(attachment["url"])
            else:
                return request.not_found()
        elif attachment["datas"]:
            data = BytesIO(base64.standard_b64decode(attachment["datas"]))
            return http.send_file(data, filename=attachment['name'], as_attachment=True)
        else:
            return request.not_found()

    @http.route(['/create_service_order'], type='http', auth="public", website=True)
    def portal_create_service_order(self, **kw):
        partner = request.env.user.partner_id
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
        related_fusion_companies = partner.last_client_id.related_company_ids

        values = {
            'client_employee_ids': client_employee_ids,
            'all_services': all_services,
            'nationalities': nationalities,
            'job_positions': job_positions,
            'related_clients': related_clients,
            'last_client_id': partner.last_client_id.id,
            'client_contracts': client_contracts,
            'related_fusion_companies': related_fusion_companies,
        }
        return request.render('ebs_fusion_theme.submit_new_service_modal', values)

    @http.route(['/get/client'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_client(self, **kw):
        partner = request.env.user.partner_id
        if partner:
            return {
                'client': [(partner.id, partner.name)],
            }

    @http.route(['/search/group_service'], type='json', auth="public", website=True)
    def get_group_service(self, **kw):
        group_id = kw.get('group_id')
        if group_id:
            service_groups = request.env['ebs.crm.service'].browse(int(group_id))
            services = service_groups.dependent_services_ids.mapped('service')
            services_name = []
            for rec in services:
                services_name.append(rec.name)
            return {
                'services_name': services_name,
                'group_name': service_groups.name
            }

    @http.route(['/submit_order'], type='http', auth="public", website=True)
    def portal_submit_order(self, **kw):
        partner = request.env.user.partner_id
        order_id = ''
        is_service_group = request.env['ebs.crm.service'].sudo().search([('id', '=', int(kw.get('services')))])
        template_id = request.env['ebs.crm.service.template'].sudo().search([('service_id', '=', is_service_group.id)],
                                                                            limit=1)
        if not template_id:
            is_service_group.set_ready()
            template_id = request.env['ebs.crm.service.template'].sudo().search(
                [('service_id', '=', is_service_group.id)],
                limit=1)
        create_vals = {

            'partner_id': partner.id,
            'client_id': partner.parent_id.id,
            'generated_from_portal': True,
            'service_id': int(kw.get('services')),
            'service_template_id': template_id.id,

        }

        if kw.get('urgent'):
            create_vals.update({'is_urgent': True})

        proposal_id = request.env['ebs.crm.proposal'].sudo().search(
            [
                ('contact_id', '=', partner.id),
                ('state', '=', 'sign')])
        if proposal_id:
            flag = False
            line_id = ''

            if line_id and flag:
                if not line_id.add_service_process:
                    create_vals.update({'proposal_line_id': line_id.id, })
                    order_id = request.env['ebs.crm.service.process'].sudo().create(create_vals)
                else:
                    order_id = request.env['ebs.crm.service.process'].sudo().create(create_vals)
            else:
                order_id = request.env['ebs.crm.service.process'].sudo().create(create_vals)
        else:
            order_id = request.env['ebs.crm.service.process'].sudo().create(create_vals)
        if is_service_group.is_group:
            counter = 1

        users = request.env['res.users'].sudo().search([])
        for user in users:
            if user.has_group('ebs_fusion_services.group_services_manager'):
                body = "The Service order is requested by %s" % (partner.name)
                activity_type_id = request.env['mail.activity.type'].sudo().search([('name', '=', 'To Do')])
                vals = {
                    'activity_type_id': activity_type_id.id,
                    'res_model_id': request.env['ir.model']._get('res.partner').id,
                    'res_id': user.partner_id.id,
                    'note': body,
                    'user_id': user.id,
                }
                request.env['mail.activity'].sudo().create(vals)

        return werkzeug.utils.redirect('/my/service_orders')

    @http.route(['/my/service_orders', '/my/service_orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_service_orders(self, page=1, date_begin=None, date_end=None, sortby=None, search=None,
                                 search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        ServiceOrder = request.env['ebs.crm.service.process']

        domain = [
            '|', ('partner_id', '=', request.env.user.partner_id.id), ('client_id', '=', partner.last_client_id.id)
        ]
        menu_name = ''
        if kw.get('status'):
            domain.append(('status', '=', kw.get('status')))
            if kw.get('status') == 'draft':
                menu_name = 'New Services'
            if kw.get('status') == 'ongoing':
                menu_name = 'Under Process'
            if kw.get('status') == 'onhold':
                menu_name = 'OnHold'
            if kw.get('status') == 'completed':
                menu_name = 'Completed'
            if kw.get('status') == 'cancelled':
                menu_name = 'Cancelled'
        searchbar_sortings = {
            'start_date': {'label': _('Start Date'), 'order': 'start_date desc'},
            'due_date': {'label': _('Due Date'), 'order': 'due_date desc'},
            'service_order_date': {'label': _('Service Order Date'), 'order': 'service_order_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('State'), 'order': 'status'},
        }
        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('SO Sequence'), 'type': 'text'},
            'service_order_date': {'input': 'service_order_date', 'label': _('Date'), 'type': 'date'},
            'service_id': {'input': 'service_id', 'label': _('Service'), 'type': 'text'},
            'partner_id': {'input': 'partner_id', 'label': _('Beneficiary'), 'type': 'text'},
            'status': {'input': 'status', 'label': _('Status'), 'type': 'text'},
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>'),
                        'type': 'text'},
        }

        # default sortby order
        if not sortby:
            sortby = 'service_order_date'
        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        if search and search_in:
            search_domain = []
            if search_in == 'name':
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in == 'service_order_date':
                search_domain = OR([search_domain, [('service_order_date', 'ilike', search)]])
            if search_in == 'service_id':
                service_id = request.env['ebs.crm.service'].sudo().search([('name', 'ilike', search)])
                search_domain = OR([search_domain, [('service_id', 'in', service_id.ids)]])
            if search_in == 'partner_id':
                partner_ids = request.env['res.partner'].sudo().search([('name', 'ilike', search)])
                search_domain = OR([search_domain, [('partner_id', 'in', partner_ids.ids)]])
            if search_in == 'status':
                if search == 'active':
                    search = 'ongoing'
                elif search == 'pending':
                    search = 'onhold'
                elif search == 'closed':
                    search = 'completed'
                search_domain = OR([search_domain, [('status', 'ilike', search)]])
            if search_in == 'content':
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('status', 'ilike', search)]])
            domain += search_domain

        # count for pager
        service_count = ServiceOrder.sudo().search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/service_orders",
            url_args={'status': kw.get('status')},
            total=service_count,
            page=page,
            step=10
        )
        # search the count to display, according to the pager data
        services = ServiceOrder.sudo().search(domain, order=sort_order, limit=10, offset=pager['offset'])
        request.session['service_history'] = services.ids[:100]
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
            'services': services.sudo(),
            'page_name': 'service_order',
            'pager': pager,
            'default_url': '/my/service_order?',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search': search,
            'search_in': search_in,
            'employee_ids': employee_ids,
            'client_employee_ids': client_employee_ids,
            'all_services': all_services,
            'nationalities': nationalities,
            'job_positions': job_positions,
            'related_clients': related_clients,
            'last_client_id': partner.last_client_id.id,
            'client_contracts': client_contracts,
            'so_menu_name': menu_name,
        })
        return request.render("ebs_fusion_services.portal_my_services", values)

    @http.route(['/services'], type='http', auth="public", website=True)
    def portal_services_menu(self, **kw):
        values = {
            'page_name': 'services',
            'main_service_menu': True,
        }
        return request.render("ebs_fusion_services.portal_services_menu", values)

    @http.route(['/my/service_orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_service_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False,
                                  **kw):
        partner = request.env.user.partner_id
        try:
            order_sudo = self._document_check_access('ebs.crm.service.process', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type,
                                     report_ref='service_management.action_report_service_order', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if order_sudo and request.session.get(
                'view_quote_%s' % order_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % order_sudo.id] = now
            body = _('Quotation viewed by customer %s') % order_sudo.partner_id.name
            _message_post_helper('ebs.crm.service.process', order_sudo.id, body, token=order_sudo.access_token,
                                 message_type='notification', subtype_xmlid="mail.mt_note")
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
        if order_sudo.status == 'draft':
            parent_menu_name = 'New Services'
        if order_sudo.status == 'ongoing':
            parent_menu_name = 'Under Process'
        if order_sudo.status == 'onhold':
            parent_menu_name = 'OnHold'
        if order_sudo.status == 'completed':
            parent_menu_name = 'Completed'
        if order_sudo.status == 'cancelled':
            parent_menu_name = 'Cancelled'
        values = {
            'service_order': order_sudo,
            'message': message,
            'employee_ids': employee_ids,
            'client_employee_ids': client_employee_ids,
            'all_services': all_services,
            'nationalities': nationalities,
            'job_positions': job_positions,
            'related_clients': related_clients,
            'client_contracts': client_contracts,
            'last_client_id': partner.last_client_id.id,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'report_type': 'html',
            'parent_url': '/my/service_orders?status=%s' % order_sudo.status,
            'parent_menu_name': parent_menu_name,
            'action': request.env.ref('ebs_fusion_services.ebs_fusion_crm_proposal_process_action'),
        }

        return request.render('ebs_fusion_services.service_order_portal_template', values)

    @http.route(['/my/sub_service_orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_sub_service_order_page(self, order_id, report_type=None, access_token=None, message=False,
                                      download=False,
                                      **kw):
        partner = request.env.user.partner_id
        try:
            order_sudo = self._document_check_access('ebs.crm.service.process', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type,
                                     report_ref='service_management.action_report_service_order', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        partner_id = request.env.user.partner_id
        client_id = partner_id.last_client_id
        related_clients = request.env['ebs.client.contact'].sudo().search([('partner_id', '=', partner.id)]).mapped(
            'client_id')
        client_contracts = request.env['ebs.crm.proposal'].sudo().search(
            [('contact_id', '=', client_id.id), ('type', '=', 'proposal'), ('state', '=', 'active')])

        values = {
            'sub_service_order': order_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'related_clients': related_clients,
            'client_contracts': client_contracts,
            'last_client_id': partner_id.last_client_id.id,
            'report_type': 'html',
            'action': request.env.ref('ebs_fusion_services.ebs_fusion_crm_proposal_process_action'),
        }

        return request.render('ebs_fusion_services.sub_service_order_portal_template', values)
