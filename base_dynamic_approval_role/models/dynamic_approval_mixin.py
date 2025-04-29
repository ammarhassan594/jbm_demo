# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from lxml import etree


class DynamicApprovalMixin(models.AbstractModel):
    _inherit = "dynamic.approval.mixin"

    role_distribution_id = fields.Many2one(comodel_name="role.distribution", copy=False)

    @api.model
    def fields_view_get(
            self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if view_type == "form" and not self._tier_validation_manual_config:
            doc = etree.XML(res["arch"])
            for node in doc.xpath("/form/sheet/group[@name='approvals']"):
                str_element = self.env["ir.qweb"]._render("base_dynamic_approval_role.role_distribution_template")
                node.addprevious(etree.fromstring(str_element))
            View = self.env["ir.ui.view"]
            new_arch, new_fields = View.postprocess_and_fields(doc,self._name)
            res["arch"] = new_arch

            # We don't want to loose previous configuration, so, we only want to add
            # the new fields

            new_fields.update(res["fields"])
            res["fields"] = new_fields
            if self._name == 'manpower.transfer':
                domain = [('related_to', '=', 'manpower')]
                if domain:
                    if res['fields'].get('role_distribution_id'):
                        res['fields']['role_distribution_id']['domain'] = domain
        return res
