from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class IrRuleInherit(models.Model):
    _inherit = 'ir.rule'

    def _get_rules(self, model_name, mode='read'):
        query = """ SELECT r.id FROM ir_rule r JOIN ir_model m ON (r.model_id=m.id)
                                WHERE m.model=%s AND r.active AND r.perm_{mode} AND r.id IN %s
                                AND (r.id IN (SELECT rule_group_id FROM rule_group_rel rg
                                              JOIN res_groups_users_rel gu ON (rg.group_id=gu.gid)
                                              WHERE gu.uid=%s)
                                     OR r.global)
                                ORDER BY r.id
                            """.format(mode=mode)

        base_query = """ SELECT r.id FROM ir_rule r JOIN ir_model m ON (r.model_id=m.id)
                                        WHERE m.model=%s AND r.active AND r.perm_{mode} 
                                        AND (r.id IN (SELECT rule_group_id FROM rule_group_rel rg
                                                      JOIN res_groups_users_rel gu ON (rg.group_id=gu.gid)
                                                      WHERE gu.uid=%s)
                                             OR r.global)
                                        ORDER BY r.id
                                    """.format(mode=mode)
        model_list = ['sale.order',
                      'crm.lead',
                      'hr.attendance',
                      'account.move',
                      'approval.request',
                      'hr.payslip']
        if mode not in self._MODES:
            raise ValueError('Invalid mode: %r' % (mode,))
        if self.env.su:
            return self.browse(())
        if self.env.user.has_group('jbm_group_access_right_extended.group_crm_manager') and model_name == 'crm.lead':
            return self.env.ref('jbm_group_access_right_extended.jbm_crm_manager_rule')
        elif (self.env.user.has_group(
                'jbm_group_access_right_extended.custom_accountant_role_manager') or self.env.user.has_group(
            'jbm_group_access_right_extended.custom_accounting_auditor_manager')) and model_name in model_list:
            record_rules = []
            if model_name == 'crm.lead':
                record_rules = [self.env.ref('jbm_group_access_right_extended.jbm_crm_manager_rule').id]
            # elif model_name == 'hr.attendance':
            #     record_rules = [self.env.ref('jbm_group_access_right_extended.hr_attendance_rule_of_read_only').id,
            #                     self.env.ref('jbm_group_access_right_extended.hr_attendance_rule_of_read_only_test').id]
            elif model_name == 'sale.order':
                record_rules = [self.env.ref('jbm_group_access_right_extended.ir_rule_of_sale_order_for_read_only').id,
                                self.env.ref(
                                    'jbm_group_access_right_extended.ir_rule_of_sale_order_for_read_only_test').id]
            elif model_name == 'account.move':
                record_rules = [self.env.ref('jbm_group_access_right_extended.jbm_rule_of_read_only_vendor_bill').id,
                                self.env.ref('jbm_group_access_right_extended.jbm_rule_of_journal_entry').id,
                                self.env.ref('jbm_group_access_right_extended.jbm_rule_of_others_move_types').id
                                ]
            elif model_name == 'approval.request':
                record_rules = [
                    self.env.ref('jbm_group_access_right_extended.jbm_rule_for_only_and_his_child_approval_request').id]

            elif model_name == 'hr.payslip':
                record_rules = [
                    self.env.ref('jbm_group_access_right_extended.jbm_rule_of_hr_payslip_for_read').id,
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_reverse_rule_of_hr_payslip_for_read').id]
            if record_rules:
                self._cr.execute(query, (model_name, tuple(record_rules), self._uid))
            else:
                self._cr.execute(base_query, (model_name, self._uid))
            return self.browse(row[0] for row in self._cr.fetchall())
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_accounting_manager') and model_name in [
            'sale.order', 'account.move', 'approval.request', 'hr.attendance', 'hr.payslip']:
            record_rules = []
            if model_name == 'sale.order':
                record_rules = [self.env.ref('jbm_group_access_right_extended.ir_rule_of_sale_order_for_read_only').id,
                                self.env.ref(
                                    'jbm_group_access_right_extended.ir_rule_of_sale_order_for_read_only_test').id]
            elif model_name == 'account.move':
                record_rules = [self.env.ref(
                    'jbm_group_access_right_extended.jbm_rule_of_read_and_write_vendor_bill').id,
                                self.env.ref(
                                    'jbm_group_access_right_extended.rule_of_access_others_move_types').id
                                ]
            elif model_name == 'approval.request':
                record_rules = [
                    self.env.ref('jbm_group_access_right_extended.jbm_rule_for_only_and_his_child_approval_request').id]
            # elif model_name == 'hr.attendance':
            #     record_rules = [self.env.ref('jbm_group_access_right_extended.hr_attendance_rule_of_read_only').id,
            #                     self.env.ref('jbm_group_access_right_extended.hr_attendance_rule_of_read_only_test').id]

            elif model_name == 'hr.payslip':
                record_rules = [
                    self.env.ref('jbm_group_access_right_extended.jbm_rule_of_hr_payslip_for_read').id,
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_reverse_rule_of_hr_payslip_for_read').id]
            if record_rules:
                self._cr.execute(query, (model_name, tuple(record_rules), self._uid))
            else:
                self._cr.execute(base_query, (model_name, self._uid))
            return self.browse(row[0] for row in self._cr.fetchall())
        # elif self.env.user.has_group('jbm_group_access_right_extended.procurement_user_role') and model_name in [
        #     'approval.request', 'hr.attendance', 'hr.payslip']:
        #     record_rules = []
        #     if model_name == 'approval.request':
        #         record_rules = [
        #             self.env.ref('jbm_group_access_right_extended.jbm_rule_for_only_and_his_child_approval_request').id]
        #     # elif model_name == 'hr.attendance':
        #     #     record_rules = [self.env.ref('jbm_group_access_right_extended.hr_attendance_rule_of_read_only').id,
        #     #                     self.env.ref('jbm_group_access_right_extended.hr_attendance_rule_of_read_only_test').id]
        #
        #     elif model_name == 'hr.payslip':
        #         record_rules = [
        #             self.env.ref('jbm_group_access_right_extended.jbm_rule_of_hr_payslip_for_read').id,
        #             self.env.ref(
        #                 'jbm_group_access_right_extended.jbm_reverse_rule_of_hr_payslip_for_read').id]
        #     if record_rules:
        #         self._cr.execute(query, (model_name, tuple(record_rules), self._uid))
        #     else:
        #         self._cr.execute(base_query, (model_name, self._uid))
        #     return self.browse(row[0] for row in self._cr.fetchall())
        # elif self.env.user.has_group('jbm_group_access_right_extended.custom_procurement_manager') and model_name in [
        #     'hr.attendance', 'approval.request', 'hr.payslip']:
        #     record_rules = []
        #     # if model_name == 'hr.attendance':
        #     #     record_rules = [
        #     #         self.env.ref('jbm_group_access_right_extended.rule_of_jbm_attendance_manager_only_read').id,
        #     #         self.env.ref('jbm_group_access_right_extended.rule_reverse_of_jbm_attendance_manager_only_read').id]
        #     if model_name == 'approval.request':
        #         record_rules = [
        #             self.env.ref('jbm_group_access_right_extended.jbm_rule_for_only_and_his_child_approval_request').id]
        #     elif model_name == 'hr.payslip':
        #         record_rules = [
        #             self.env.ref('jbm_group_access_right_extended.jbm_rule_of_hr_payslip_for_read').id,
        #             self.env.ref(
        #                 'jbm_group_access_right_extended.jbm_reverse_rule_of_hr_payslip_for_read').id]
        #     if record_rules:
        #         self._cr.execute(query, (model_name, tuple(record_rules), self._uid))
        #     else:
        #         self._cr.execute(base_query, (model_name, self._uid))
        #     return self.browse(row[0] for row in self._cr.fetchall())
        elif (self.env.user.has_group(
                'jbm_group_access_right_extended.custom_committee_user') or self.env.user.has_group(
            'jbm_group_access_right_extended.custom_committee_leader')) and model_name in [
            'hr.payslip', 'approval.request', 'hr.attendance']:
            record_rules = []
            if model_name == 'approval.request':
                record_rules = [
                    self.env.ref('jbm_group_access_right_extended.jbm_rule_for_only_and_his_child_approval_request').id]
            elif model_name == 'hr.payslip':
                record_rules = [
                    self.env.ref('jbm_group_access_right_extended.jbm_rule_of_hr_payslip_for_read').id,
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_reverse_rule_of_hr_payslip_for_read').id]
            # elif model_name == 'hr.attendance':
            #     record_rules = [
            #         self.env.ref('jbm_group_access_right_extended.hr_attendance_rule_of_read_only').id,
            #         self.env.ref('jbm_group_access_right_extended.hr_attendance_rule_of_read_only_test').id]
            if record_rules:
                self._cr.execute(query, (model_name, tuple(record_rules), self._uid))
            else:
                self._cr.execute(base_query, (model_name, self._uid))
            return self.browse(row[0] for row in self._cr.fetchall())
        elif (self.env.user.has_group(
                'jbm_group_access_right_extended.custom_hr_user') or self.env.user.has_group(
            'jbm_group_access_right_extended.custom_hr_manager')) and model_name == 'approval.request':
            record_rules = []
            if model_name == 'approval.request':
                record_rules = [
                    self.env.ref('jbm_group_access_right_extended.jbm_rule_for_only_and_his_child_approval_request').id]
            if record_rules:
                self._cr.execute(query, (model_name, tuple(record_rules), self._uid))
            else:
                self._cr.execute(base_query, (model_name, self._uid))
            return self.browse(row[0] for row in self._cr.fetchall())
        elif (self.env.user.has_group(
                'jbm_group_access_right_extended.custom_general_manager_representative') or self.env.user.has_group(
            'jbm_group_access_right_extended.custom_general_manager')) and model_name in [
            'sale.order', 'account.move', 'approval.request', 'hr.contract', 'hr.attendance', 'hr.payslip',
            'hr.appraisal', 'sale.order.line']:
            record_rules = []
            if model_name in ['sale.order', 'sale.order.line']:
                record_rules = [
                    self.env.ref('jbm_group_access_right_extended.ir_rule_of_sale_order_for_read_and_write').id,
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_reveres_rule_of_sale_order_for_read_and_write').id]
            elif model_name == 'account.move':
                record_rules = [
                    self.env.ref('jbm_group_access_right_extended.jbm_rule_of_read_only_journal_entry').id,
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_rule_of_read_and_write_vendor_bill').id,
                    self.env.ref('jbm_group_access_right_extended.jbm_rule_of_others_move_types').id]
            elif model_name == 'approval.request':
                record_rules = [
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_rule_of_create_and_read_approval_request').id,
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_reverse_rule_of_create_and_read_approval_request').id]
            elif model_name == 'hr.contract':
                record_rules = [
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_rule_of_read_only_contract').id,
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_reverse_rule_of_read_only_contract').id]
            # elif self.env.user.has_group(
            #         'jbm_group_access_right_extended.custom_general_manager_representative') and model_name == 'hr.attendance':
            #     record_rules = [
            #         self.env.ref(
            #             'jbm_group_access_right_extended.rule_of_jbm_attendance_manager_only_read').id,
            #         self.env.ref(
            #             'jbm_group_access_right_extended.rule_reverse_of_jbm_attendance_manager_only_read').id]
            # elif self.env.user.has_group(
            #         'jbm_group_access_right_extended.custom_general_manager') and model_name == 'hr.attendance':
            #     record_rules = [
            #         self.env.ref(
            #             'jbm_group_access_right_extended.hr_attendance_rule_of_read_and_write').id,
            #         self.env.ref(
            #             'jbm_group_access_right_extended.reverse_rule_of_attendance_read_and_write').id]

            elif model_name == 'hr.payslip':
                record_rules = [
                    self.env.ref('jbm_group_access_right_extended.jbm_rule_of_hr_payslip_for_read').id,
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_reverse_rule_of_hr_payslip_for_read').id]

            if record_rules:
                self._cr.execute(query, (model_name, tuple(record_rules), self._uid))
            else:
                self._cr.execute(base_query, (model_name, self._uid))
            return self.browse(row[0] for row in self._cr.fetchall())
        elif self.env.user.has_group(
                'jbm_group_access_right_extended.custom_financial_manager') and model_name in [
            'sale.order', 'account.move', 'approval.request', 'hr.attendance', 'hr.payslip',
            'sale.order.line']:
            record_rules = []
            if model_name in ['sale.order', 'sale.order.line']:
                record_rules = [
                    self.env.ref('jbm_group_access_right_extended.ir_rule_of_sale_order_for_read_and_write').id,
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_reveres_rule_of_sale_order_for_read_and_write').id]
            elif model_name == 'account.move':
                record_rules = [
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_rule_of_read_and_write_vendor_bill').id,
                    self.env.ref('jbm_group_access_right_extended.rule_of_access_others_move_types').id]
            elif model_name == 'approval.request':
                record_rules = [
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_rule_of_create_and_read_approval_request').id,
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_reverse_rule_of_create_and_read_approval_request').id]
            # elif model_name == 'hr.attendance':
            #     record_rules = [
            #         self.env.ref(
            #             'jbm_group_access_right_extended.hr_attendance_rule_of_read_only').id,
            #         self.env.ref(
            #             'jbm_group_access_right_extended.hr_attendance_rule_of_read_only_test').id]
            elif model_name == 'hr.payslip':
                record_rules = [
                    self.env.ref('jbm_group_access_right_extended.jbm_rule_of_hr_payslip_for_read').id,
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_reverse_rule_of_hr_payslip_for_read').id]
            if record_rules:
                self._cr.execute(query, (model_name, tuple(record_rules), self._uid))
            else:
                self._cr.execute(base_query, (model_name, self._uid))

            return self.browse(row[0] for row in self._cr.fetchall())
        elif self.env.user.has_group(
                'jbm_group_access_right_extended.custom_group_shared_service_manager') \
                and model_name in ['hr.attendance']:
            record_rules = []
            # if model_name == 'hr.attendance':
            #     record_rules = [
            #         self.env.ref(
            #             'jbm_group_access_right_extended.rule_of_jbm_attendance_manager').id]
            if record_rules:
                self._cr.execute(query, (model_name, tuple(record_rules), self._uid))
            else:
                self._cr.execute(base_query, (model_name, self._uid))
            return self.browse(row[0] for row in self._cr.fetchall())
        elif self.env.user.has_group(
                'jbm_group_access_right_extended.custom_group_shared_service_manager') and model_name == 'approval.request':
            record_rules = []
            if model_name == 'approval.request':
                record_rules = [
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_rule_of_create_and_read_approval_request').id,
                    self.env.ref(
                        'jbm_group_access_right_extended.jbm_reverse_rule_of_create_and_read_approval_request').id
                ]
            if record_rules:
                self._cr.execute(query, (model_name, tuple(record_rules), self._uid))
            else:
                self._cr.execute(base_query, (model_name, self._uid))
            return self.browse(row[0] for row in self._cr.fetchall())
        else:
            return super(IrRuleInherit, self)._get_rules(model_name, mode=mode)

    # def _compute_domain(self, model_name, mode="read"):
    #     res = super(IrRuleInherit, self)._compute_domain(model_name, mode)
    #     obj_list = ['account.move']
    #     if model_name in obj_list:
    #         if mode != 'read' and self.env.context.get('default_move_type') == 'in_invoice':
    #             raise ValidationError(_('user can not done (%s) operation..! (%s)') % (mode, self.env.user.name))
    #     return res
