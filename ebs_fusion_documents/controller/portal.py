from odoo import fields, http, _
import werkzeug
import base64
from odoo.http import request, content_disposition
from datetime import datetime, date
from io import BytesIO
from werkzeug.utils import redirect
from odoo.osv.expression import OR, AND
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager


class CustomerPortal(CustomerPortal):
    def _neuter_mimetype(self, mimetype, user):
        wrong_type = 'ht' in mimetype or 'xml' in mimetype or 'svg' in mimetype
        if wrong_type and not user._is_system():
            return 'text/plain'
        return mimetype

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Docs = request.env['documents.document']
        date_after_month = datetime.today() + relativedelta(months=1)
        renewal_docs_count = Docs.sudo().search_count([
            ('owner_id', '=', request.env.user.id), ('expiry_date', '<=', date_after_month),
            ('expiry_date', '>=', datetime.today())
        ])
        expired_docs_count = Docs.sudo().search_count([
            ('owner_id', '=', request.env.user.id),
            ('expiry_date', '<=', datetime.today())
        ])
        docs_count = Docs.sudo().search_count([
            ('owner_id', '=', request.env.user.id),
        ])
        values.update({
            'renewal_docs_count': renewal_docs_count,
            'expired_docs_count': expired_docs_count,
            'docs_count': docs_count,
        })
        return values

    @http.route(['/search/document_type'], type='json', auth="public", methods=['POST'],
                website=True)
    def document_type(self, **kw):
        document_type_id = request.env['ebs.document.type'].sudo().search([('id', '=', int(kw.get('doc_type_id')))])
        return {
            'required': document_type_id.has_issue_expiry_date,
        }

    @http.route(['/upload_document'], type='http', auth="public", website=True)
    def portal_upload_document(self, **kw):
        partner = request.env.user.partner_id
        document_types = request.env['ebs.document.type'].sudo().search([])
        values = {
            'companies': partner.related_company_ids,
            'lines': [],
            'page_name': 'newdoc',
            'doc_types': document_types,
        }
        return request.render('ebs_fusion_documents.upload_document', values)

    @http.route(['/submit_document'], type='http', auth="public", website=True)
    def portal_submit_document(self, **post):
        partner = request.env.user.partner_id
        name = post.get('doc_file').filename
        file = post.get('doc_file')
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
        return werkzeug.utils.redirect('/my/docs/%s' % (document_id.id))

    @http.route(['/my/renewal_docs', '/my/renewal_docs/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_renewal_docs(self, page=1, date_begin=None, date_end=None, sortby=None, search=None,
                               search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Docs = request.env['documents.document']
        Legal_doc_types = request.env['ebs.document.type'].sudo().search([('is_legal', '=', True)])
        date_after_month = datetime.today() + relativedelta(months=1)
        domain = [
            ('owner_id', '=', request.env.user.id), ('expiry_date', '<=', date_after_month),
            ('expiry_date', '>=', datetime.today()),
            ('folder_id.name', '=', 'Legal')
        ]

        searchbar_sortings = {
            'expiry_date': {'label': _('Expiry Date'), 'order': 'expiry_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'number': {'label': _('Document Number'), 'order': 'document_number'},
        }
        searchbar_inputs = {
            'number': {'input': 'number', 'label': _('Document Number')},
            'name': {'input': 'name', 'label': _('Name')},
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
        }

        # default sortby order
        if not sortby:
            sortby = 'expiry_date'
        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        if search and search_in:
            search_domain = []
            if search_in in ('number'):
                search_domain = OR([search_domain, [('document_number', 'ilike', search)]])
            if search_in in ('name'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('content'):
                search_domain = OR(
                    [search_domain, ['|', ('name', 'ilike', search), ('document_number', 'ilike', search)]])
            domain += search_domain

        # count for pager
        renewal_docs_count = Docs.sudo().search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/renewal_docs",

            total=renewal_docs_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        renewal_docs = Docs.sudo().search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['renewal_docs_history'] = renewal_docs.ids[:100]
        print(renewal_docs, "@@")

        values.update({
            'date': date_begin,
            'renewal_docs': renewal_docs.sudo(),
            'page_name': 'renewal_docs',
            'pager': pager,

            'default_url': '/my/renewal_docs',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search': search,
            'search_in': search_in,
        })
        print(values, "@@@values============")
        return request.render("ebs_fusion_documents.portal_my_renewal_docs", values)

    @http.route(['/my/expired_docs', '/my/expired_docs/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_expired_docs(self, page=1, date_begin=None, date_end=None, sortby=None, search=None,
                               search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Docs = request.env['documents.document']
        Legal_doc_types = request.env['ebs.document.type'].sudo().search([('is_legal', '=', True)])
        domain = [
            ('owner_id', '=', request.env.user.id),
            ('expiry_date', '<=', datetime.today()),
            ('folder_id.name', '=', 'Legal')
        ]

        searchbar_sortings = {
            'expiry_date': {'label': _('Expiry Date'), 'order': 'expiry_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'number': {'label': _('Document Number'), 'order': 'document_number'},
        }
        searchbar_inputs = {
            'number': {'input': 'number', 'label': _('Document Number')},
            'name': {'input': 'name', 'label': _('Name')},
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
        }

        # default sortby order
        if not sortby:
            sortby = 'expiry_date'
        sort_order = searchbar_sortings[sortby]['order']

        # archive_groups = self._get_archive_groups('documents.document', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        if search and search_in:
            search_domain = []
            if search_in in ('number'):
                search_domain = OR([search_domain, [('document_number', 'ilike', search)]])
            if search_in in ('name'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('content'):
                search_domain = OR(
                    [search_domain, ['|', ('name', 'ilike', search), ('document_number', 'ilike', search)]])
            domain += search_domain

        # count for pager
        expired_docs_count = Docs.sudo().search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/expired_docs",

            total=expired_docs_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        expired_docs = Docs.sudo().search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['expired_docs_history'] = expired_docs.ids[:100]
        print(expired_docs, "@@----------------------------------------")

        values.update({
            'date': date_begin,
            'expired_docs': expired_docs.sudo(),
            'page_name': 'expired_docs',
            'pager': pager,

            'default_url': '/my/expired_docs',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search': search,
            'search_in': search_in,
        })
        print(values, "@@@values============")
        return request.render("ebs_fusion_documents.portal_my_expired_docs", values)

    @http.route(['/my/docs/<int:order_id>'], type='http', auth="public", website=True)
    def portal_docs_page(self, order_id, report_type=None, access_token=None, message=False, download=False,
                         **kw):
        try:
            order_sudo = self._document_check_access('documents.document', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        all_services = request.env['ebs.crm.service'].sudo().search([], order='category_id')
        employee_ids = request.env['hr.employee'].sudo().search([])
        nationalities = request.env['res.country'].sudo().search([])
        job_positions = request.env['hr.job'].sudo().search([])
        partner_id = request.env.user.partner_id
        # client_id = partner_id.last_client_id
        # related_clients = request.env['ebs.client.contact'].sudo().search([('partner_id', '=', partner_id.id)]).mapped(
        #     'client_id')
        # client_contracts = request.env['ebs.crm.proposal'].sudo().search(
        #     [('contact_id', '=', client_id.id), ('type', '=', 'proposal'), ('state', '=', 'active')])
        # client_employee_ids = request.env['hr.employee'].sudo().search(
        #     [('partner_parent_id', '=', client_id.id)])
        values = {
            'doc': order_sudo,
            'message': message,
            'token': access_token,
            'page_name': 'docs',
            'bootstrap_formatting': True,
            # 'last_client_id': partner_id.last_client_id.id,
            'partner_id': order_sudo.partner_id.id,
            'all_services': all_services,
            # 'client_employee_ids': client_employee_ids,
            'employee_ids': employee_ids,
            'nationalities': nationalities,
            'job_positions': job_positions,
            # 'related_clients': related_clients,
            # 'client_contracts': client_contracts,
            'report_type': 'html',
            'action': request.env.ref('documents.document_action'),
        }

        now = fields.Date.today()
        date_after_month = date.today() + relativedelta(months=1)

        print(values, "page-3333333333333333333------------------")

        return request.render('ebs_fusion_documents.docs_portal_template', values)

    @http.route(['/my/docs', '/my/docs/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_docs(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, folder=None,
                       search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        client_contacts = request.env['res.partner'].sudo().search([('parent_id', '=', partner.parent_id.id)])
        Docs = request.env['documents.document']
        Legal_doc_types = request.env['ebs.document.type'].sudo().search([('is_legal', '=', True)])
        domain = []
        domain = ['|', ('partner_id', '=', partner.parent_id.id), ('partner_id', 'in', client_contacts.ids)]
        if folder:
            if not folder == 'all':
                domain = AND([domain, [('folder_id', '=', int(folder))]])
        print(domain, "####################################3domain")
        searchbar_sortings = {
            'status': {'label': _('Status'), 'order': 'status'},
            'issue_date': {'label': _('Issue Date'), 'order': 'issue_date desc'},
            'expiry_date': {'label': _('Expiry Date'), 'order': 'expiry_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'number': {'label': _('Document Number'), 'order': 'document_number'},
        }
        searchbar_inputs = {
            'number': {'input': 'number', 'label': _('Document Number')},
            'name': {'input': 'name', 'label': _('Name')},
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
        }

        # default sortby order
        if not sortby:
            sortby = 'expiry_date'
        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        if search and search_in:
            search_domain = []
            if search_in in ('number'):
                search_domain = OR([search_domain, [('document_number', 'ilike', search)]])
            if search_in in ('name'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('content'):
                search_domain = OR(
                    [search_domain, ['|', ('name', 'ilike', search), ('document_number', 'ilike', search)]])
            domain += search_domain

        # count for pager
        docs_count = Docs.sudo().search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/docs",
            total=docs_count,
            page=page,
            step=10
        )
        # search the count to display, according to the pager data
        docs = Docs.sudo().search(domain, order=sort_order, limit=10, offset=pager['offset'])
        request.session['docs_history'] = docs.ids[:100]
        print(docs, "@@----------------------------------------")
        employee_ids = request.env['hr.employee'].sudo().search([])
        all_services = request.env['ebs.crm.service'].sudo().search([], order='category_id')
        nationalities = request.env['res.country'].sudo().search([])
        job_positions = request.env['hr.job'].sudo().search([])
        folders = request.env['documents.folder'].sudo().search([])
        # related_clients = request.env['ebs.client.contact'].sudo().search([('partner_id', '=', partner.id)]).mapped(
        #     'client_id')
        # client_contracts = request.env['ebs.crm.proposal'].sudo().search(
        #     [('contact_id', '=', partner.last_client_id.id), ('type', '=', 'proposal'), ('state', '=', 'active')])

        # client_employee_ids = request.env['hr.employee'].sudo().search(
        #     [('partner_parent_id', '=', partner.last_client_id.id)])
        values.update({
            'date': date_begin,
            'docs': docs.sudo(),
            'page_name': 'docs',
            'pager': pager,

            'default_url': '/my/docs',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search': search,
            'search_in': search_in,
            'employee_ids': employee_ids,
            'all_services': all_services,
            # 'client_employee_ids': client_employee_ids,
            'nationalities': nationalities,
            'job_positions': job_positions,
            # 'related_clients': related_clients,
            # 'client_contracts': client_contracts,
            # 'last_client_id': partner.last_client_id.id,
            'folders': folders,
        })
        print(values, "@@@values============")
        return request.render("ebs_fusion_documents.portal_my_docs", values)

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
            print(attachment["datas"], "3333")
            data = BytesIO(base64.standard_b64decode(attachment["datas"]))
            return http.send_file(data, filename=attachment['name'], as_attachment=True)
        else:
            return request.not_found()

    @http.route('/web/binary/download_document', type='http', auth="public")
    def download_document(self, model, field, id, filename=None, **kw):
        """ Download link for files stored as binary fields.
        :param str model: name of the model to fetch the binary from
        :param str field: binary field
        :param str id: id of the record from which to fetch the binary
        :param str filename: field holding the file's name, if any
        :returns: :class:`werkzeug.wrappers.Response`
        """
        Model = request.env[model]
        res = Model.browse([int(id)])
        filecontent = res.file
        if not filecontent:
            return request.not_found()
        else:
            if not filename:
                filename = '%s_%s' % (model.replace('.', '_'), id)
            return request.make_response(filecontent,
                                         [('Content-Type', 'application/octet-stream'),
                                          ('Content-Disposition', content_disposition(filename))])
