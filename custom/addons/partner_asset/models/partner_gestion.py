
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

try:
   import qrcode
except ImportError:
   qrcode = None
try:
   import base64
except ImportError:
   base64 = None
from io import BytesIO


class Entreprise(models.Model):
    _name = 'partner.entreprise'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Gestion des entreprises de gestion des bornes'

    name = fields.Char(string='Nom', required=True)
    contact = fields.Char(string='Contact')
    country_id = fields.Many2one('res.country', string='Pays')
    street = fields.Char(string='Rue')
    city = fields.Char(string='Ville')
    email = fields.Char(string='Adresse e-mail')
    commission = fields.Float(string='Commission (%)')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, readonly=True, required=True)
    borne_ids = fields.Many2many('partner.asset', string='Bornes',tracking=True)
    asset_ids = fields.One2many('partner.asset.company', 'entreprise_id' , string='Assigne des bornes aux gestionnaires',tracking=True)
    latitude = fields.Float(string='Geo Latitude', digits=(10, 7))
    longitude = fields.Float(string='Geo Longitude', digits=(10, 7))

    @api.model
    def create(self, vals):
        # Store the latitude and longitude from the hidden fields
        if 'latitude' in vals:
            vals['latitude'] = float(vals['latitude'])
        if 'longitude' in vals:
            vals['longitude'] = float(vals['longitude'])

        return super(Entreprise, self).create(vals)

    def write(self, vals):
        # Store the latitude and longitude from the hidden fields
        if 'latitude' in vals:
            vals['latitude'] = float(vals['latitude'])
        if 'longitude' in vals:
            vals['longitude'] = float(vals['longitude'])

        return super(Entreprise, self).write(vals)

    def get_map_values(self):
        # Return latitude and longitude to be used in the view
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
        }



ASSIGNMENT_STATE = [('draft', 'Brouillon'), ('to_approve', 'En attente de validation'), ('done', 'Valide'), ('cancel', 'Annule')]

class PartnerAssetCompany(models.Model):
    _name = 'partner.asset.company'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Gestion des bornes aux Societe"
    _check_company_auto = True
    
    
    @api.model
    def _get_default_name(self):
        return self.env["ir.sequence"].next_by_code("assignment.code")
    
    name = fields.Char(required=True, default='/', tracking=True)
    asset_id = fields.Many2one('partner.asset', string="Borne", domain="[('active', '=', True)]", tracking=True, check_company=True)
    lot_number = fields.Char(string='Numero serie', store=True)
    entreprise_id = fields.Many2one('partner.entreprise', string='Entreprise', tracking=True)
    date = fields.Date(string="Date de déploiement", default=fields.Date.today, tracking=True)
    state = fields.Selection(selection=ASSIGNMENT_STATE, default='draft', tracking=True)
    company_id = fields.Many2one('res.company', 'Company',  default=lambda self: self.env.company, readonly=True, required=True)
    latitude = fields.Float(string='Geo Latitude', digits=(10, 7), related='entreprise_id.latitude')
    longitude = fields.Float(string='Geo Longitude', digits=(10, 7),related='entreprise_id.longitude')
    
    
    def button_to_approve(self):
        self.write({'state': 'to_approve'})
        
    def action_validate(self):
        self.asset_id.write({'assign_gestion_id': self.id})
        self.write({'state': 'done'})
    
    def button_cancel(self):
        #self.asset_id.unlink()
        self.write({'state': 'draft'})
    
    def action_do_cancel(self):
        self.asset_id.write({'assign_gestion_id':False})
        self.write({'state': 'cancel'})
    
    
    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(with_company=vals['company_id']).next_by_code('assignment.code') or '/'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('assignment.code') or '/'
        res = super(PartnerAssetCompany, self).create(vals)
        return res
    
    def write(self, vals):
        res = super(PartnerAssetCompany, self).write(vals)
        return res
    
    def unlink(self):
        #if self.state in ('done'):
        #    raise ValidationError(_('Vous ne pouvez pas supprimer une assignation déja validée'))
        #self.asset_id.unlink()
        return super(PartnerAssetCompany, self).unlink()
    