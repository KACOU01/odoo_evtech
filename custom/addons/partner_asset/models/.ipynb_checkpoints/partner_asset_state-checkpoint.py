# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PartnerAssetState(models.Model):
    _name = 'partner.asset.state'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Partner asset state description"
    
    
    name = fields.Char()
    sequence = fields.Integer(help='Used to order the note stages')
    
    
    _sql_constraints = [('partner_asset_state_name_unique', 'unique(name)', 'State name already exists')]
    