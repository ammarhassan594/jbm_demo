from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta


class PayslipCustom(models.Model):
    _inherit = 'hr.payslip'


    def get_emp_pensions(self, payslip, employee, rule_code, basic, basicded, mobile, mobileded,
                         accomm, accommded, transport, transded, social, socialded):
        amount = 0.0
        pension_obj = self.env['pension.config'].search([('country_id', '=', employee.country_id.id)],
                                                        limit=1)
        if pension_obj:
            if not employee.out_of_pension:
                # basic_salary = basic + basicded
                # social = social + socialded
                # housing = accomm + accommded
                # transport = transport + transded
                # mobile = mobile + mobileded
                if employee.joining_date > payslip.date_from:
                    basic_salary = basic * (30 - employee.joining_date.day + 1) / 30
                    social = social * (30 - employee.joining_date.day + 1) / 30
                    housing = accomm * (30 - employee.joining_date.day + 1) / 30
                    transport = transport * (30 - employee.joining_date.day + 1) / 30
                    mobile = mobile * (30 - employee.joining_date.day + 1) / 30
                else:
                    basic_salary = basic
                    social = social
                    housing = accomm
                    transport = transport
                    mobile = mobile
                emp_basic = pension_obj.employee_basic / 100
                emp_social = pension_obj.employee_social / 100
                emp_housing = pension_obj.employee_housing / 100
                emp_transport = pension_obj.employee_transport / 100
                emp_mobile = pension_obj.employee_mobile / 100
                employer_basic = pension_obj.employer_basic / 100
                employer_soc = pension_obj.employer_social / 100
                employer_housing = pension_obj.employer_housing / 100
                employer_transport = pension_obj.employer_transport / 100
                employer_mobile = pension_obj.employer_mobile / 100
                max_emp_limit = pension_obj.employee_max_limit

                if rule_code == 'PE':
                    if employee.joining_date and pension_obj.applied_on_date:
                        if employee.joining_date < pension_obj.applied_on_date:
                            basic, social, housing, transport, mobile = self._get_pension_element_values(
                                basic_salary,
                                social,
                                housing,
                                transport,
                                mobile,
                                pension_obj,
                                'employee')
                            amount = basic * emp_basic + social * emp_social + housing * emp_housing + mobile * emp_mobile + transport * emp_transport
                        else:
                            if max_emp_limit:
                                if basic_salary >= max_emp_limit:
                                    basic_salary = max_emp_limit
                                    social = housing = mobile = transport = 0
                                elif (basic_salary + social) >= max_emp_limit:
                                    social = social - (basic_salary + social - max_emp_limit)
                                    housing = mobile = transport = 0
                                elif (basic_salary + social + housing) >= max_emp_limit:
                                    housing = housing - (basic_salary + social + housing - max_emp_limit)
                                    transport = mobile = 0
                                elif (basic_salary + social + housing + transport) >= max_emp_limit:
                                    transport = transport - (
                                            basic_salary + social + housing + transport - max_emp_limit)
                                    mobile = 0
                                elif (basic_salary + social + housing + transport + mobile) >= max_emp_limit:
                                    mobile = mobile - (
                                            basic_salary + social + housing + transport + mobile - max_emp_limit)
                            basic, social, housing, transport, mobile = self._get_pension_element_values(
                                basic_salary,
                                social,
                                housing,
                                transport,
                                mobile,
                                pension_obj,
                                'employee')
                            amount = basic * emp_basic + social * emp_social + housing * emp_housing + mobile * emp_mobile + transport * emp_transport
                    else:
                        basic, social, housing, transport, mobile = self._get_pension_element_values(
                            basic_salary,
                            social,
                            housing,
                            transport,
                            mobile,
                            pension_obj,
                            'employee')
                        amount = basic * emp_basic + social * emp_social + housing * emp_housing + mobile * emp_mobile + transport * emp_transport


                elif rule_code == 'PER':
                    if employee.joining_date and pension_obj.applied_on_date:
                        if employee.joining_date < pension_obj.applied_on_date:
                            if max_emp_limit:
                                if basic_salary >= max_emp_limit:
                                    basic_salary = max_emp_limit
                                    social = housing = mobile = transport = 0
                                elif (basic_salary + social) >= max_emp_limit:
                                    social = social - (basic_salary + social - max_emp_limit)
                                    housing = mobile = transport = 0
                                elif (basic_salary + social + housing) >= max_emp_limit:
                                    housing = housing - (basic_salary + social + housing - max_emp_limit)
                                    transport = mobile = 0
                                elif (basic_salary + social + housing + transport) >= max_emp_limit:
                                    transport = transport - (
                                            basic_salary + social + housing + transport - max_emp_limit)
                                    mobile = 0
                                elif (basic_salary + social + housing + transport + mobile) >= max_emp_limit:
                                    mobile = mobile - (
                                            basic_salary + social + housing + transport + mobile - max_emp_limit)
                            # print('amounts', max_emp_limit, basic_salary, social, housing, mobile, transport)
                            basic, social, housing, transport, mobile = self._get_pension_element_values(
                                basic_salary,
                                social,
                                housing,
                                transport,
                                mobile,
                                pension_obj,
                                'employer')

                            amount = basic * employer_basic + social * employer_soc + housing * employer_housing + mobile * \
                                     employer_mobile + transport * employer_transport
                        else:
                            basic, social, housing, transport, mobile = self._get_pension_element_values(
                                basic_salary,
                                social,
                                housing,
                                transport,
                                mobile,
                                pension_obj,
                                'employer')
                            basic = basic_salary * employer_basic
                            social = social * employer_soc
                            housing = housing * employer_housing
                            mobile = mobile * employer_mobile
                            transport = transport * employer_transport
                            amount = basic + social + housing + mobile + transport
                    else:
                        amount = basic_salary * employer_basic + social * employer_soc + housing * employer_housing + mobile * \
                                 employer_mobile + transport * employer_transport
        return amount

    def _get_pension_element_values(self, basic_salary, social, housing, transport, mobile, pension_obj, code):
        max_basic = pension_obj.employee_basic_limit if code == 'employee' else pension_obj.employer_basic_limit
        max_social = pension_obj.employee_social_limit if code == 'employee' else pension_obj.employer_social_limit
        max_housing = pension_obj.employee_housing_limit if code == 'employee' else pension_obj.employer_housing_limit
        max_mobile = pension_obj.employee_mobile_limit if code == 'employee' else pension_obj.employer_mobile_limit
        max_transport = pension_obj.employee_transport_limit if code == 'employee' else pension_obj.employer_transport_limit
        basic = min(max_basic, basic_salary) if max_basic else basic_salary
        social = min(max_social, social) if max_social else social
        housing = min(max_housing, housing) if max_housing else housing
        transport = min(max_transport, transport) if max_transport else transport
        mobile = min(max_mobile, mobile) if max_mobile else mobile
        return basic, social, housing, transport, mobile

