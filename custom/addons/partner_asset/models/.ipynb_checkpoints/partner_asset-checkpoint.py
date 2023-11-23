# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PartnerAsset(models.Model):
    _name = 'partner.asset
    _description = "Partner asset description"
    
    name = fields.Char()
    description = fields.Html("Asset Description", help="Add a note about this asset")
    active = fields.Boolean('Active', default=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Client")
    company_id = fields.Many2one('res.company', 'Company',  default=lambda self: self.env.company)
    reference = fields.Char()
    asset_model = fields.Many2one('partner.asset.model', string='Model')
    