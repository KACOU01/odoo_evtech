# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    partner_asset_ids = fields.Many2many('partner.asset', compute='_compute_partner_asset_ids', string='Partner Assets')

    @api.depends('partner_id.asset_ids')
    def _compute_partner_asset_ids(self):
        for order in self:
            order.partner_asset_ids = order.partner_id.asset_ids