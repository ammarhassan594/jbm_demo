from odoo import models, fields, api


class InheritHrPayslip(models.Model):
    _inherit = "hr.payslip"

    attendance_sheet_id = fields.Many2one(comodel_name="attendance.sheet", string="Attendance Sheet",
                                          compute='_compute_attendance_sheet_id')

    def _compute_attendance_sheet_id(self):
        for rec in self:
            rec.attendance_sheet_id = self.env['attendance.sheet'].sudo().search(
                [('batch_id.payslip_batch_id', '=', rec.payslip_run_id.id), ('employee_id', '=', rec.employee_id.id)],
                limit=1)

    def view_related_attendance_sheet(self):
        self.ensure_one()
        return {
            'name': 'Attendance Sheet',
            'res_model': 'attendance.sheet',
            'res_id': self.attendance_sheet_id.id,
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def get_basic_deduction(self, payslip, employee):
        basic_deduction_amount = 0
        if payslip.attendance_sheet_id:
            if payslip.date_to > employee.contract_id.date_end and employee.out_of_attendance:
                basic_deduction_amount += payslip.attendance_sheet_id.basic_deduction_termination
                basic_deduction_amount = 0 - basic_deduction_amount

            else:
                basic_deduction_amount += payslip.attendance_sheet_id.basic_deduction_tot
                basic_deduction_amount = 0 - basic_deduction_amount
        return basic_deduction_amount

    def get_other_deduction(self, payslip, employee):
        other_deduction_amount = 0
        if payslip.attendance_sheet_id:
            if payslip.date_to > employee.contract_id.date_end and employee.out_of_attendance:
                other_deduction_amount += payslip.attendance_sheet_id.other_deduction_termination
                other_deduction_amount = 0 - other_deduction_amount
            else:
                other_deduction_amount += payslip.attendance_sheet_id.other_deduction_tot
                other_deduction_amount = 0 - other_deduction_amount
        return other_deduction_amount

    def get_transportation_deduction(self, payslip, employee):
        other_transportation_deduction = 0
        if payslip.attendance_sheet_id:
            if payslip.date_to > employee.contract_id.date_end and employee.out_of_attendance:
                other_transportation_deduction += payslip.attendance_sheet_id.transportation_deduction_termination
                other_transportation_deduction = 0 - other_transportation_deduction

            else:
                other_transportation_deduction += payslip.attendance_sheet_id.transportation_deduction_tot
                other_transportation_deduction = 0 - other_transportation_deduction
        return other_transportation_deduction

    def get_housing_deduction(self, payslip, employee):
        housing_deduction = 0
        if payslip.attendance_sheet_id:
            if payslip.date_to > employee.contract_id.date_end and employee.out_of_attendance:
                housing_deduction += payslip.attendance_sheet_id.housing_deduction_termination
                housing_deduction = 0 - housing_deduction

            else:
                housing_deduction += payslip.attendance_sheet_id.housing_deduction_tot
                housing_deduction = 0 - housing_deduction
        return housing_deduction

    def get_mobile_deduction(self, payslip, employee):
        mobile_deduction = 0
        if payslip.attendance_sheet_id:
            if payslip.date_to > employee.contract_id.date_end and employee.out_of_attendance:
                mobile_deduction += payslip.attendance_sheet_id.mobile_deduction_termination
                mobile_deduction = 0 - mobile_deduction

            else:
                mobile_deduction += payslip.attendance_sheet_id.mobile_deduction_tot
                mobile_deduction = 0 - mobile_deduction
        return mobile_deduction

    def get_social_deduction(self, payslip, employee):
        social_deduction = 0
        if payslip.attendance_sheet_id:
            if payslip.date_to > employee.contract_id.date_end and employee.out_of_attendance:
                social_deduction += payslip.attendance_sheet_id.social_deduction_termination
                social_deduction = 0 - social_deduction

            else:
                social_deduction += payslip.attendance_sheet_id.social_deduction_tot
                social_deduction = 0 - social_deduction
        return social_deduction

    def get_car_deduction(self, payslip, employee):
        car_deduction = 0
        if payslip.attendance_sheet_id:
            if payslip.date_to > employee.contract_id.date_end and employee.out_of_attendance:
                car_deduction += payslip.attendance_sheet_id.car_deduction_termination
                car_deduction = 0 - car_deduction

            else:
                car_deduction += payslip.attendance_sheet_id.car_deduction_tot
                car_deduction = 0 - car_deduction
        return car_deduction

    def get_supervision_deduction(self, payslip, employee):
        supervision_deduction = 0
        if payslip.attendance_sheet_id:
            if payslip.date_to > employee.contract_id.date_end and employee.out_of_attendance:
                supervision_deduction += payslip.attendance_sheet_id.supervision_deduction_termination
                supervision_deduction = 0 - supervision_deduction

            else:
                supervision_deduction += payslip.attendance_sheet_id.supervision_deduction_tot
                supervision_deduction = 0 - supervision_deduction
        return supervision_deduction

    def get_deduction_settlement(self, payslip, employee):
        deduction_settlement = 0
        if payslip.attendance_sheet_id:
            deduction_settlement += payslip.attendance_sheet_id.deduction_settlement
            deduction_settlement = 0 - deduction_settlement
        return deduction_settlement

    def get_eobs_deduction(self, payslip, employee):
        eobs_deduction = 0
        if payslip.attendance_sheet_id:
            if payslip.date_to > employee.contract_id.date_end and employee.out_of_attendance:
                eobs_deduction += payslip.attendance_sheet_id.eobs_deduction_termination
                eobs_deduction = 0 - eobs_deduction

            else:
                eobs_deduction += payslip.attendance_sheet_id.eobs_deduction_tot
                eobs_deduction = 0 - eobs_deduction
        return eobs_deduction

    def get_incentive_deduction(self, payslip, employee):
        monthly_deduction = 0
        if payslip.attendance_sheet_id:
            if payslip.date_to > employee.contract_id.date_end and employee.out_of_attendance:
                monthly_deduction += payslip.attendance_sheet_id.monthly_incentive_deduction_termination
                monthly_deduction = 0 - monthly_deduction

            else:
                monthly_deduction += payslip.attendance_sheet_id.monthly_incentive_deduction_tot
                monthly_deduction = 0 - monthly_deduction
        return monthly_deduction

    def get_representative_deduction(self, payslip, employee):
        representative_deduction = 0
        if payslip.attendance_sheet_id:
            if payslip.date_to > employee.contract_id.date_end and employee.out_of_attendance:
                representative_deduction += payslip.attendance_sheet_id.representative_deduction_termination
                representative_deduction = 0 - representative_deduction

            else:
                representative_deduction += payslip.attendance_sheet_id.representative_deduction_tot
                representative_deduction = 0 - representative_deduction
        return representative_deduction

    def get_work_condition_deduction(self, payslip, employee):
        work_condition_deduction = 0
        if payslip.attendance_sheet_id:
            if payslip.date_to > employee.contract_id.date_end and employee.out_of_attendance:
                work_condition_deduction += payslip.attendance_sheet_id.work_condition_deduction_termination
                work_condition_deduction = 0 - work_condition_deduction

            else:
                work_condition_deduction += payslip.attendance_sheet_id.work_condition_deduction_tot
                work_condition_deduction = 0 - work_condition_deduction
        return work_condition_deduction

    def get_basic_allowance(self, payslip, employee):
        basic_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                basic_allowance += payslip.attendance_sheet_id.basic_allowance_tot
        return basic_allowance

    def get_earning_settlement(self, payslip, employee):
        earning_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                earning_allowance += payslip.attendance_sheet_id.earning_allowance
        return earning_allowance

    def get_car_allowance(self, payslip, employee):
        car_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                car_allowance += payslip.attendance_sheet_id.car_allowance_tot
        return car_allowance

    def get_social_allowance(self, payslip, employee):
        social_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                social_allowance += payslip.attendance_sheet_id.social_allowance_tot
        return social_allowance

    def get_housing_allowance(self, payslip, employee):
        housing_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                housing_allowance += payslip.attendance_sheet_id.housing_allowance_tot
        return housing_allowance

    def get_transportation_allowance(self, payslip, employee):
        transportation_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                transportation_allowance += payslip.attendance_sheet_id.transportation_allowance_tot
        return transportation_allowance

    def get_other_allowance(self, payslip, employee):
        other_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                other_allowance += payslip.attendance_sheet_id.other_allowance_tot
        return other_allowance

    def get_mobile_allowance(self, payslip, employee):
        mobile_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                mobile_allowance += payslip.attendance_sheet_id.mobile_allowance_tot
        return mobile_allowance

    def get_supervision_allowance(self, payslip, employee):
        supervision_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                supervision_allowance += payslip.attendance_sheet_id.supervision_allowance_tot
        return supervision_allowance

    def get_eobs_allowance(self, payslip, employee):
        eobs_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                eobs_allowance += payslip.attendance_sheet_id.eobs_allowance_tot
        return eobs_allowance

    def get_incentive_allowance(self, payslip, employee):
        monthly_incentive_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                monthly_incentive_allowance += payslip.attendance_sheet_id.monthly_incentive_allowance_tot
        return monthly_incentive_allowance

    def get_representative_allowance(self, payslip, employee):
        representative_monthly_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                representative_monthly_allowance += payslip.attendance_sheet_id.representative_monthly_allowance_tot
        return representative_monthly_allowance

    def get_work_condition_allowance(self, payslip, employee):
        work_condition_allowance = 0
        if payslip:
            if payslip.attendance_sheet_id:
                work_condition_allowance += payslip.attendance_sheet_id.work_condition_allowance_tot
        return work_condition_allowance
