# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    assignment_ids = fields.One2many('partner.asset.assignment', 'partner_id')
    asset_nbr = fields.Integer('Nombre de congélateur', compute='_compute_asset_nbr', store=True)
    assignment_id = fields.Many2one('partner.asset.assignment', string="Congelateur")
    model_asset = fields.Many2one(related='assignment_id.asset_model', store=True)
    asset_ids = fields.Many2many('partner.asset', compute="_compute_asset_ids",store=True)
    
    @api.depends('assignment_ids')
    def _compute_asset_ids(self):
        for rec in self:
            rec.asset_ids = rec.assignment_ids.asset_id
    
    @api.depends('assignment_ids')
    def _compute_asset_nbr(self):
        for rec in self:
            rec.asset_nbr = len(rec.assignment_ids)
    
    @api.onchange('assignment_ids')
    def _onchange_assgnement(self):
        for rec in self:
            if rec.assignment_ids:
                rec.assignment_id = rec.assignment_ids[0]
    
    def _actualise_assgnement(self):
        for rec in self:
            if rec.assignment_ids:
                rec.assignment_id = rec.assignment_ids[0]
    
    def button_asset_upgrade(self):
        for rec in self:
            if rec.assignment_ids:
                rec.assignment_id = rec.assignment_ids[0]
            
    def action_view_asset_assignment(self):
        action = self.env['ir.actions.act_window']._for_xml_id('partner_asset.action_asset_config_assignment')
        action["domain"] = [("partner_id", "=", self.id)]
        action["context"] = {'default_partner_id': self.id}
        return action
