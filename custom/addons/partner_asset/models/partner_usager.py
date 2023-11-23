
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

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
    

    def action_payer(self):
        for paiement in self:
            if paiement.usager_id.balance >= paiement.amount:
                paiement.usager_id.balance -= paiement.amount
            else:
                raise ValidationError("Solde insuffisant pour effectuer le paiement.")

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
