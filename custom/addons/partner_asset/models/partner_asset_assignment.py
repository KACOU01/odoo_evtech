# -*- coding: utf-8 -*-

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



ASSIGNMENT_STATE = [('draft', 'Brouillon'), ('to_approve', 'En attente de validation'), ('done', 'Valide'), ('cancel', 'Annule')]

class PartnerAssetAssignment(models.Model):
    _name = 'partner.asset.assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Asset assignment description"
    
    
    @api.model
    def _get_default_name(self):
        return self.env["ir.sequence"].next_by_code("assignment.code")
    
    name = fields.Char(required=True, default='/', tracking=True)
    asset_id = fields.Many2one('partner.asset', string="Borne", domain="[('is_assign', '=', False), ('active', '=', True)]", tracking=True,)
    partner_id = fields.Many2one('res.partner', string='Client', tracking=True)
    contract_id = fields.Many2one('partner.contract', string='Contrat')

    date = fields.Date(string="Date de déploiement", default=fields.Date.today, tracking=True)
    state = fields.Selection(selection=ASSIGNMENT_STATE, default='draft', tracking=True)
    company_id = fields.Many2one('res.company', 'Company',  default=lambda self: self.env.company, readonly=True, required=True)
    qr_code = fields.Binary('QRcode', compute="_generate_qr")
    # asset_model = fields.Many2one(related='asset_id.asset_model', store=True)
    street = fields.Char(string='Rue')
    city = fields.Char(string='Ville')
    latitude = fields.Float(string='Geo Latitude', digits=(10, 7))
    longitude = fields.Float(string='Geo Longitude', digits=(10, 7))
    

    # Méthode pour initialiser la carte Leaflet
    # def _init_map(self):
    #     for record in self:
    #         record.env['ir.ui.view'].call_template("web_leaflet_assets.map_init_script", {"map_id": "map", "latitude": record.latitude, "longitude": record.longitude})


    
    def button_to_approve(self):
        self.write({'state': 'to_approve'})
        
    def action_validate(self):
        self.asset_id.write({'assignment_id': self.id})
        self.write({'state': 'done'})
    
    def button_cancel(self):
        #self.asset_id.unlink()
        self.write({'state': 'draft'})
    
    def action_do_cancel(self):
        self.asset_id.write({'assignment_id':False})
        self.write({'state': 'cancel'})
    
    def _generate_qr(self):
       "method to generate QR code"
       for rec in self:
           if qrcode and base64:
               qr = qrcode.QRCode(
                   version=1,
                   error_correction=qrcode.constants.ERROR_CORRECT_L,
                   box_size=3,
                   border=4,
               )
               qr.add_data("Borne : ")
               qr.add_data(rec.asset_id.name)
               qr.add_data(", Client : ")
               qr.add_data(rec.partner_id.name)
               qr.make(fit=True)
               img = qr.make_image()
               temp = BytesIO()
               img.save(temp, format="PNG")
               qr_image = base64.b64encode(temp.getvalue())
               rec.update({'qr_code':qr_image})
           else:
               raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))
    
    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(with_company=vals['company_id']).next_by_code('assignment.code') or '/'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('assignment.code') or '/'
        res = super(PartnerAssetAssignment, self).create(vals)
        return res
    
    def write(self, vals):
        res = super(PartnerAssetAssignment, self).write(vals)
        return res
    
    def unlink(self):
        #if self.state in ('done'):
        #    raise ValidationError(_('Vous ne pouvez pas supprimer une assignation déja validée'))
        #self.asset_id.unlink()
        return super(PartnerAssetAssignment, self).unlink()
    
    