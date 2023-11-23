# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PartnerAssetModel(models.Model):
    _name = 'partner.asset.model'
    _order = 'name asc'

    name = fields.Char('Model name', required=True)
    vendors = fields.Many2many('res.partner', string='Vendeur')
    active = fields.Boolean(default=True)
    asset_type = fields.Selection([('type_1', 'Type 1'), ('type_2', 'Type 2')], default='type_1', required=True)
    volume = fields.Float('Volume (m3)')
    asset_count = fields.Integer()
    model_year = fields.Integer()
    color = fields.Char()
    power = fields.Integer('Power')