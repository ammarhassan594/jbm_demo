from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class ContractSignature(models.Model):
    _name = 'hr.contract.signature'
    _description = 'HR Contract Signature'

    name = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=False)
    hr_contract_id = fields.Many2one(
        comodel_name='hr.contract',
        string='Contract',
        required=True, ondelete='cascade')
    signature = fields.Char(string='Signature')
    sequence = fields.Integer(
        string='Sequence',
        required=False)

    def write(self, vals):
        old_user = self.name.id
        new_user = vals.get('name', '')
        old_sequence = self.name.id
        new_sequence = vals.get('sequence', '')

        if (old_user != new_user and new_user != '') or (old_sequence != new_sequence and new_sequence != ''):
            raise ValidationError(_("Sequence and User can't be modified"))

        current_user = self.env.uid

        if old_user != current_user:
            raise ValidationError(_("Only related user can fill the signature"))

        current_sequence = self.sequence

        remaining_signatures = self.env['hr.contract.signature'].search(
            [('hr_contract_id', '=', self.hr_contract_id.id), ('id', '!=', self.id), ('signature', '!=', False)],
            order='sequence asc', limit=1)
        if len(remaining_signatures) > 0:
            lowest_remaining_signature = remaining_signatures[0]
            if lowest_remaining_signature.sequence < current_sequence:
                raise ValidationError(_("Previous signature must be filled"))

        res = super(ContractSignature, self).write(vals)

        rem_signatures = self.env['hr.contract.signature'].search(
            [('hr_contract_id', '=', self.hr_contract_id.id), ('id', '!=', self.id), ('signature', '=', False)],
            order='sequence asc')

        if len(rem_signatures)>0:
            first_signature = min(rem_signatures, key=lambda x: x.sequence)
            first_user = first_signature.name if first_signature else None

            msg = _(
                'A signature is required by ') + ': <a href=# data-oe-model=res.users data-oe-id=%d>%s</a>' % (
                      first_user.id, first_user.name)
            for rec in self:
                rec.hr_contract_id.message_post(body=msg)

        return res
