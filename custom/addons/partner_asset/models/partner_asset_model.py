# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from odoo.exceptions import UserError,ValidationError,RedirectWarning
class PartnerAssetModel(models.Model):
    _name = 'partner.asset.model'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Describe asset model"
    _order = 'name asc'
    

    name = fields.Char('Nom Modele', required=True)
    vendors = fields.Many2many('res.partner', string='Vendeur')
    active = fields.Boolean('Active', default=True)
    asset_type = fields.Selection([('type_1', 'Type 1'), ('type_2', 'Type 2')])
    price = fields.Float('Prix')
    asset_ids = fields.One2many('partner.asset', 'asset_model')
    asset_count = fields.Integer(string='Nbre Borne', compute="_compute_asset_count")
    company_id = fields.Many2one('res.company', 'Company',  default=lambda self: self.env.company, required=True)


    @api.depends('asset_ids')
    def _compute_asset_count(self):
        for rec in self:
            rec.asset_count = len(rec.asset_ids)
            
    
    _sql_constraints = [('partner_name_price_unique', 'unique(name)', 'reference name already exists')]
    
    
    @api.model
    def create(self,vals):
        res = super(PartnerAssetModel, self).create(vals)
        return res
    
    def write(self, vals):
        res = super(PartnerAssetModel, self).write(vals)
        return res
    
    def unlink(self):
        if len(self.asset_ids) > 0 :
            raise ValidationError(_('Vous ne pouvez pas supprimer un modele qui contient des Borne'))
        return super(PartnerAssetModel, self).unlink()
    