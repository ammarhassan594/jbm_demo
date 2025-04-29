from odoo import models, fields, api, _


class ResConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_terms_condition_ar = fields.Html(string="Terms And Condition",
                                              related='company_id.purchase_terms_condition_ar',
                                              readonly=False, )
    purchase_terms_condition_en = fields.Html(string="Terms And Condition",
                                              related='company_id.purchase_terms_condition_en',

                                             readonly=False, )

    purchase_stamp_width = fields.Float(string="Stamp Width (cm)",
                                        config_parameter='taqat_purchase_extended.purchase_stamp_width')

    purchase_stamp_height = fields.Float(string="Stamp Height (cm)",
                                         config_parameter='taqat_purchase_extended.purchase_stamp_height')

    purchase_signature_width = fields.Float(string="Signature width (cm)",
                                            config_parameter='taqat_purchase_extended.purchase_signature_width')

    purchase_signature_height = fields.Float(string="Signature height (cm)",
                                             config_parameter='taqat_purchase_extended.purchase_signature_height')

    purchase_note_en = fields.Html(string="Not (English)")
    purchase_note_ar = fields.Html(string="Not (Arabic)")

    @api.model
    def get_values(self):
        res = super(ResConfigSetting, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        purchase_note_en = params.get_param('purchase_note_en')
        purchase_note_ar = params.get_param('purchase_note_ar')
        res.update(
            purchase_note_en=purchase_note_en,
            purchase_note_ar=purchase_note_ar
        )
        return res

    def set_values(self):
        super(ResConfigSetting, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("purchase_note_en", self.purchase_note_en)
        self.env['ir.config_parameter'].sudo().set_param("purchase_note_ar", self.purchase_note_ar)


class CompanyInherit(models.Model):
    _inherit = 'res.company'

    purchase_terms_condition_ar = fields.Html(string="Terms And Condition",
                                              readonly=False,
                                              default='''
                                                        <li style="direction:rtl;">
                                                            التسليم: خلال 1 يوم عمل بعد
                                                            <br></br>
                                                            <span>استلام أمر الشراء</span>
                                                            <!--                                    <br></br>-->
                                                            <!--                                    <span>أمر الشراء</span>-->
                                                        </li>
                                                        <li style="direction:rtl;">
                                                            <span>الدفع: تحويل بنكي</span>
                                                            <br></br>
                                                            <span>بعد الاستلام</span>
                                                            <br></br>
                                                            <span>حد أقصي 15 يوم عمل.</span>
                                                        </li>
                        
                                                        <li style="direction:rtl;">
                                                            <span>غرامة تأخير التوريد: 1 % على كل</span>
                                                            <br></br>
                                                            <span>يوم تأخير بحد</span>
                                                            <br></br>
                                                            <span>أقصى 10% من القيمة الإجمالية</span>
                                                            <br></br>
                                                            <span>لطلب الشراء.</span>
                                                        </li>''')
    purchase_terms_condition_en = fields.Html(string="Terms And Condition",
                                              readonly=False,
                                              default='''<li>Delivery Time: within 1
                                                            <br></br>
                                                            <span>work day after LPO</span>
                                                        </li>
                                                        <li>
                                                            <span>Payment: Bank Transfer</span>
                                                            <br></br>
                                                            <span>after Delivery within</span>
                                                            <br></br>
                                                            <span>15-day max.</span>
                                                        </li>
                        
                                                        <li>
                                                            <span>Penalty Delivery delay: 1%</span>
                                                            <br></br>
                                                            <span>on each day of delay up to</span>
                                                            <br></br>
                                                            <span>a maximum of 10% of the</span>
                                                            <br></br>
                                                            <span>total purchase order.</span>
                                                        </li>''')
