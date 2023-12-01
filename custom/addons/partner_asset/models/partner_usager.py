
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
import pandas as pd
try:
   import qrcode
except ImportError:
   qrcode = None
try:
   import base64
except ImportError:
   base64 = None
from io import BytesIO


_ASSET_STATE = [('draf', 'Brouillons'), ('confirm', 'Confimer'),('cancel','Annuler')]

class PartnerPayment(models.Model):
    _name = 'partner.payment.usage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Partner Payment"

    
    @api.model
    def _get_default_name(self):
        return self.env["ir.sequence"].next_by_code("payment.code")
    
    name = fields.Char(required=True, default='/', tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    company_id = fields.Many2one('res.company', 'Company',  default=lambda self: self.env.company, tracking=True, readonly=True, required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(currency_field='currency_id', store=True, string="Montant",tracking=True)
    date = fields.Date(string="Date")
    asset_id = fields.Many2one('partner.asset', string='Borne', tracking=True)
    partner_id = fields.Many2one('res.partner', related='asset_id.partner_id', string='Client', store=True,tracking=True)
    state = fields.Selection(selection=_ASSET_STATE, string="Etat",tracking=True)
    usager_id = fields.Many2one('partner.usager', string='Usager', store=True,tracking=True)
    commission = fields.Float(string='Commission',related='company_id.commission',store=True,tracking=True)
    amount_commission = fields.Monetary(currency_field='currency_id', store=True, string="Commission",tracking=True,compute='_compute_amount_commission')
    methode_paiement = fields.Selection([
        ('carte_credit', 'Carte de crédit'),
        ('espece', 'Espèces')
    ], string='Méthode de paiement',default='espece')



    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(with_company=vals['company_id']).next_by_code('payment.code') or '/'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('payment.code') or '/'
        res = super(PartnerPayment, self).create(vals)
        return res
    
    def write(self, vals):
        res = super(PartnerPayment, self).write(vals)
        return res
    
    def unlink(self):
        #if self.state in ('done'):
        #    raise ValidationError(_('Vous ne pouvez pas supprimer une assignation déja validée'))
        #self.asset_id.unlink()
        return super(PartnerPayment, self).unlink()

    @api.model
    def import_payments_from_excel(self):
        # Open file picker dialog
        return {
            'name': _('Upload Excel File'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'form',
            'view_id': self.env.ref('base.view_attachment_form').id,
            'view_ids': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_res_model': 'partner.payment.usage',
                'default_res_id': 0,
                'default_res_field': 'file',
            },
        }

    @api.model
    def process_uploaded_file(self, attachment_id):
        try:
            attachment = self.env['ir.attachment'].browse(attachment_id)
            if attachment and attachment.res_model == 'partner.payment.usage' and attachment.res_field == 'file':
                # Process the file content (you can call your import function here)
                file_content = attachment.datas.decode('utf-8')
                self.import_payments_from_excel_(file_content)
            else:
                raise ValidationError(_("Invalid file. Please try again."))

        except Exception as e:
            raise ValidationError(_("An error occurred while processing the file: %s" % str(e)))

    def import_payments_from_excel_(self, file_path):
        try:
            df = pd.read_excel(file_path)

            for index, row in df.iterrows():
                usager_name = row.get('Usager')  # Replace 'Usager' with the actual column name in your Excel file

                # Check if the usager exists
                # usager = self.env['partner.usager'].search([('name', '=', usager_name)])
                # if not usager:
                #     raise ValidationError(_("Usager '%s' not found. Please create the usager first." % usager_name))

                payment_data = {
                    'name': row['Name'],  # Replace 'Name' with the actual column name in your Excel file
                    'amount': row['Amount'],  # Replace 'Amount' with the actual column name in your Excel file
                    # 'usager_id': usager.id,
                    # Add other fields as needed
                }

                self.create(payment_data)

            return True

        except Exception as e:
            raise ValidationError(_("An error occurred while importing payments: %s" % str(e)))

    def action_payer(self):
        for paiement in self:
            if paiement.usager_id.balance >= paiement.amount:
                paiement.usager_id.balance -= paiement.amount
            else:
                raise ValidationError("Solde insuffisant pour effectuer le paiement.")

    def create_or_get_usager(self, usager_name):
        usager = self.env['partner.usager'].search([('name', 'ilike', usager_name)])
        if not usager:
            usager = self.env['partner.usager'].create({'name': usager_name})
        return usager

    def create_or_get_borne(self, borne_name):
        borne = self.env['partner.asset'].search([('name', 'ilike', borne_name)])
        if not borne:
            borne = self.env['partner.asset'].create({'name': borne_name})
        return borne

    @api.depends('amount', 'commission')
    def _compute_amount_commission(self):
        for payment in self:
            payment.amount_commission = payment.amount * (payment.commission / 100)

class Usager(models.Model):
    _name = 'partner.usager'
    _description = 'Gestion des usagers'

    name = fields.Char(string='Nom', required=True)
    phone = fields.Char(string='Telephone',)
    balance = fields.Float(string='Solde')
