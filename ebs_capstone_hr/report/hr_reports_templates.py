# import base64
# import threading
#
# from odoo import models, fields, api, _
# from odoo.exceptions import AccessError, RedirectWarning, UserError
# try:
#     from docx import Document
# except ImportError:
#     pass
# try:
#     from docx.enum.text import WD_ALIGN_PARAGRAPH
# except ImportError:
#     pass
# # from docx.shared import Inches, Cm, RGBColor
# try:
#     from docx.shared import Pt
# except ImportError:
#     pass
# # from docx.oxml import OxmlElement
# # from docx.oxml.ns import qn
# # from docx.enum.table import WD_ROW_HEIGHT_RULE
#
# from datetime import datetime
#
#
# class HrReportsTemplates(models.Model):
#     _inherit = "hr.employee"
#
#     def letter_to_embassy(self):
#         document = Document()
#         title = ''
#         he_she = ''
#         if self.gender == "male":
#             title = 'Mr '
#             he_she = 'he'
#         else:
#             title = 'Ms '
#             he_she = 'she'
#
#         contract = self.env['hr.contract'].search([('employee_id', '=', self.id), ('state', '=', 'open')], limit=1)
#
#         document.add_paragraph('Date: ' + str(datetime.today().strftime('%d-%m-%Y')))
#
#         p1 = document.add_paragraph()
#         run = p1.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text("To: Embassy of  _____________")
#         run.add_break()
#         run.add_text("      Doha, Qatar")
#
#         p2 = document.add_paragraph()
#         # p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
#         run = p2.add_run()
#         run.add_text("Attn: Visa section")
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(11)
#         font.bold = True
#         font.underline = True
#
#         document.add_paragraph()
#         document.add_paragraph()
#
#         p3 = document.add_paragraph()
#         run = p3.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text("Dear Sir,")
#         run.add_break()
#         run.add_break()
#         run.add_text(
#             "This is to certify that {} {}, holder of Qatar ID number # {} and {} passport number # {} is a bonafide employee with Bro Technologies. {} is working with us as {} since {} and drawing a monthly  gross salary of QR {}".format(
#                 title, self.name or "", self.ikama or "", self.country_id and self.country_id.name or "",
#                        self.passport_id or "", he_she,
#                        self.job_id and self.job_id.name or "", str(self.joining_date),
#                        contract and contract.wage or ""))
#
#         p4 = document.add_paragraph()
#         run = p4.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "This letter is being issued at the specific request of {} {} for visa purpose. Please note that Bro Technologies will not be liable for any liabilities whatsoever arising from out of any transactions made by {} {}".format(
#                 title, self.name, title, self.name))
#
#         p5 = document.add_paragraph()
#         run = p5.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "{} {}, will bear all expenses connected to {} visit.  ".format(title, self.name, he_she))
#
#         document.add_paragraph()
#         document.add_paragraph()
#
#         p6 = document.add_paragraph()
#         run = p6.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text("Yours truly, ")
#         run.add_break()
#         run.add_break()
#         run.add_text("For Bro Technologies LLC")
#
#         document.add_paragraph()
#         document.add_paragraph()
#
#         p7 = document.add_paragraph()
#         run = p7.add_run()
#         run.add_text("_______________________")
#         run.add_break()
#         run.add_text("Anthony Awkar")
#         run.add_break()
#         run.add_text("Chief Executive Officer")
#
#         return document
#
#     def employment_and_salary_certificate(self):
#         document = Document()
#         title = ''
#         he_she = ''
#         if self.gender == "male":
#             title = 'Mr '
#             he_she = 'he'
#         else:
#             title = 'Ms '
#             he_she = 'she'
#         contract = self.env['hr.contract'].search([('employee_id', '=', self.id), ('state', '=', 'open')], limit=1)
#
#         p1 = document.add_paragraph()
#         run = p1.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#
#         run.add_text("Date: {}".format(str(
#             datetime.today().strftime('%d-%m-%Y'))))
#         run.add_break()
#         run.add_text("The Manager")
#         run.add_break()
#         run.add_text("____________")
#         run.add_break()
#         run.add_text("Doha, Qatar")
#         run.add_break()
#
#         document.add_paragraph()
#
#         p2 = document.add_paragraph()
#         p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
#         run = p2.add_run()
#         run.add_text("Subject: Salary certificate")
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(11)
#         font.bold = True
#         font.underline = True
#
#         document.add_paragraph()
#
#         p2 = document.add_paragraph()
#         run = p2.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "This is to certify that {} {}, holder of Qatar ID number # {} and {} passport number # {} is employed with us as {}.{} joined our organization on {} Her/ his  present Gross salary is QR {} per month.".format(
#                 title, self.name, self.ikama or "", self.country_id and self.country_id.name or "",
#                                   self.passport_id or "", self.job_id or "", he_she, str(self.joining_date),
#                                   contract and contract.wage or ""))
#         run.add_break()
#         p3 = document.add_paragraph()
#         run = p3.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "This letter is being issued at the specific request of {} {} without any financial obligation to the company. ".format(
#                 title, self.name))
#
#         p4 = document.add_paragraph()
#         run = p4.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "If you need further information regarding her employment, please contact the undersigned. .")
#
#         p6 = document.add_paragraph()
#         run = p6.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text("Yours truly,")
#
#         run.add_break()
#         run.add_break()
#
#         p7 = document.add_paragraph()
#         run = p7.add_run()
#         run.add_text("For Bro Technologies LLC")
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         font.bold = True
#
#         p8 = document.add_paragraph()
#         run = p8.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text("_______________________")
#         run.add_break()
#         run.add_text("Anthony Awkar")
#         run.add_break()
#         run.add_text("Chief Executive Officer")
#
#         return document
#
#     def open_bank_account(self):
#         document = Document()
#         title = ''
#         he_she = ''
#         if self.gender == "male":
#             title = 'Mr '
#             he_she = 'he'
#         else:
#             title = 'Ms '
#             he_she = 'she'
#
#         contract = self.env['hr.contract'].search([('employee_id', '=', self.id), ('state', '=', 'open')], limit=1)
#
#         p1 = document.add_paragraph()
#         run = p1.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(11)
#         run.add_break()
#         run.add_text("Date: {}".format(str(
#             datetime.today().strftime('%d-%m-%Y'))))
#         run.add_break()
#         run.add_text("The Manager")
#         run.add_break()
#         run.add_text("_____________")
#         run.add_break()
#         run.add_text("Doha, Qatar")
#         document.add_paragraph()
#
#         p2 = document.add_paragraph()
#         p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
#         run = p2.add_run()
#         run.add_text("Subject: Salary certificate")
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(13)
#         font.bold = True
#         font.underline = True
#
#         document.add_paragraph()
#
#         p3 = document.add_paragraph()
#         run = p3.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "This is to certify that {} {}, holder of Qatar ID number # {} and {} passport number # {} is employed with us as {}. {} joined our organization on {}. Her/ his  present Gross salary is QR {} per month.".format(
#                 title, self.name, self.ikama or '', self.country_id and self.country_id.name or "",
#                                   self.passport_id or '', self.job_id or '', he_she, str(self.joining_date),
#                                   contract and contract.wage or ""))
#
#         p4 = document.add_paragraph()
#         run = p4.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "this letter is being issued at the specific request of {} {} for  opening a bank account with your bank without any financial obligation to the company.".format(
#                 title, self.name))
#
#         p5 = document.add_paragraph()
#         run = p5.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "If you need further information regarding her employment, please contact the undersigned. ")
#
#         p7 = document.add_paragraph()
#         run = p7.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text("Yours truly,")
#
#         p8 = document.add_paragraph()
#         run = p8.add_run()
#         run.add_text("For Bro Technologies LLC")
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         font.bold = True
#
#         document.add_paragraph()
#         document.add_paragraph()
#
#         p9 = document.add_paragraph()
#         run = p9.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text("_______________________")
#         run.add_break()
#         run.add_text("Anthony Awkar")
#         run.add_break()
#         run.add_text("Chief Executive Officer")
#
#         return document
#
#     def salary_transfer_letter(self):
#         document = Document()
#         title = ''
#         he_she = ''
#         if self.gender == "male":
#             title = 'Mr '
#             he_she = 'he'
#         else:
#             title = 'Ms '
#             he_she = 'she'
#
#         contract = self.env['hr.contract'].search([('employee_id', '=', self.id), ('state', '=', 'open')], limit=1)
#
#         p1 = document.add_paragraph()
#         run = p1.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(11)
#         run.add_break()
#         run.add_text("Date: {}".format(str(
#             datetime.today().strftime('%d-%m-%Y'))))
#         run.add_break()
#         run.add_text("The Manager")
#         run.add_break()
#         run.add_text("_____________")
#         run.add_break()
#         run.add_text("Doha, Qatar")
#         document.add_paragraph()
#
#         p2 = document.add_paragraph()
#         p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
#         run = p2.add_run()
#         run.add_text("Subject: Salary Transfer")
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(13)
#         font.bold = True
#         font.underline = True
#
#         document.add_paragraph()
#
#         p3 = document.add_paragraph()
#         run = p3.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "This is to certify that {} {}, holder of Qatar ID number # {} and {} passport number # {} is employed with us as {}. {} joined our organization on {} Her/ his  salary breakdown is as following:".format(
#                 title, self.name, self.ikama or '', self.country_id and self.country_id.name or "",
#                                   self.passport_id or '', self.job_id or '', he_she, str(self.joining_date)))
#
#         p4 = document.add_paragraph()
#         run = p4.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "BASIC:                                                                    QR{}".format(
#                 contract and contract.wage or ""))
#         run.add_break()
#         run.add_text(
#             "Housing Allowance:                                         QR{}".format(
#                 contract and contract.accommodation or ""))
#         run.add_break()
#         run.add_text(
#             "Transportation Allowance:                             QR{}".format(
#                 contract and contract.transport_allowance or ""))
#         run.add_break()
#         run.add_text(
#             "Mobile Allowance:                                             Sim Card and phone Bill are covered by the company")
#         run.add_break()
#         run.add_text(
#             "Total Package:                                                    QR{}".format(
#                 contract and contract.package or ""))
#         run.add_break()
#         font = run.font
#         font.name = 'Axiforma'
#         font.bold = True
#
#         p5 = document.add_paragraph()
#         run = p5.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "To assist {} {} in obtaining a Loan/Credit Card from your bank, we undertake to transfer the monthly salary to his/her bank account (number ...............) opening with your bank.".format(
#                 title, self.name))
#
#         p6 = document.add_paragraph()
#         run = p6.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "If {} {} resigns or his/her employment is terminated by this Company, we undertake to pay all amounts of End of Service Benefit due to him/her, after deduction of  any amount due to the company, to his/her Bank account with official communication to that respect.".format(
#                 title, self.name))
#
#         p7 = document.add_paragraph()
#         run = p7.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "The above-named employee fully understands that Bro Technologies  does not in any way hold itself responsible for any debits incurred by him and that the granting of loan is the sole discretion of your Bank.")
#
#         p8 = document.add_paragraph()
#         run = p8.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "This letter is being issued at the specific request of {} {} without any financial obligation to the company.".format(
#                 title, self.name))
#
#         p9 = document.add_paragraph()
#         run = p9.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "If you need further information regarding her employment, please contact the undersigned.")
#
#         p10 = document.add_paragraph()
#         run = p10.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text("Yours truly,")
#
#         p11 = document.add_paragraph()
#         run = p11.add_run()
#         run.add_text("For Bro Technologies LLC")
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         font.bold = True
#
#         document.add_paragraph()
#         document.add_paragraph()
#
#         p12 = document.add_paragraph()
#         run = p12.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text("_______________________")
#         run.add_break()
#         run.add_text("Mohamed Aldelaimi")
#         run.add_break()
#         run.add_text("Co-Founder & Managing Director")
#
#         return document
#
#     def salary_breakdown(self):
#         document = Document()
#         title = ''
#         he_she = ''
#         if self.gender == "male":
#             title = 'Mr '
#             he_she = 'he'
#         else:
#             title = 'Ms '
#             he_she = 'she'
#
#         contract = self.env['hr.contract'].search([('employee_id', '=', self.id), ('state', '=', 'open')], limit=1)
#
#         p1 = document.add_paragraph()
#         run = p1.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(11)
#         run.add_break()
#         run.add_text("Date: {}".format(str(
#             datetime.today().strftime('%d-%m-%Y'))))
#         run.add_break()
#         run.add_text("The Manager")
#         run.add_break()
#         run.add_text("_____________")
#         run.add_break()
#         run.add_text("Doha, Qatar")
#         document.add_paragraph()
#
#         p2 = document.add_paragraph()
#         p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
#         run = p2.add_run()
#         run.add_text("Salary Certificate")
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(13)
#         font.bold = True
#
#         document.add_paragraph()
#
#         p3 = document.add_paragraph()
#         run = p3.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "This is to certify that {} {}, holder of Qatar ID number # {} and {} passport number # {} is employed with us as {}. {} joined our organization on {} Her/ his  salary breakdown is as following:".format(
#                 title, self.name, self.ikama or '', self.country_id and self.country_id.name or "",
#                                   self.passport_id or '', self.job_id or '', he_she, str(self.joining_date)))
#
#         p4 = document.add_paragraph()
#         run = p4.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "BASIC:                                                                    QR{}".format(
#                 contract and contract.wage or ""))
#         run.add_break()
#         run.add_text(
#             "Housing Allowance:                                         QR{}".format(
#                 contract and contract.accommodation or ""))
#         run.add_break()
#         run.add_text(
#             "Transportation Allowance:                             QR{}".format(
#                 contract and contract.transport_allowance or ""))
#         run.add_break()
#         run.add_text(
#             "Mobile Allowance:                                             Sim Card and phone Bill are covered by the company")
#         run.add_break()
#         run.add_text(
#             "Total Package:                                                    QR{}".format(
#                 contract and contract.package or ""))
#         run.add_break()
#         font = run.font
#         font.name = 'Axiforma'
#         font.bold = True
#
#         p5 = document.add_paragraph()
#         run = p5.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "This letter is being issued at the specific request of {} {} without any financial obligation to the company. ".format(
#                 title, self.name))
#
#         p6 = document.add_paragraph()
#         run = p6.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text(
#             "If you need further information regarding her employment, please contact the undersigned. ")
#
#         p10 = document.add_paragraph()
#         run = p10.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text("Yours truly,")
#
#         p11 = document.add_paragraph()
#         run = p11.add_run()
#         run.add_text("For Bro Technologies LLC")
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         font.bold = True
#
#         document.add_paragraph()
#         document.add_paragraph()
#
#         p12 = document.add_paragraph()
#         run = p12.add_run()
#         font = run.font
#         font.name = 'Axiforma'
#         font.size = Pt(10)
#         run.add_text("_______________________")
#         run.add_break()
#         run.add_text("Anthony Awkar")
#         run.add_break()
#         run.add_text("Chief Executive")
#
#         return document
