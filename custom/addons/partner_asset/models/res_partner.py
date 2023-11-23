# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    is_supplier = fields.Boolean(string='Est un Fournisseur', default=False,store=True)
    is_customer = fields.Boolean(string='Est un client',default=False,store=True)
    
    assignment_ids = fields.One2many('partner.asset.assignment', 'partner_id')
    asset_nbr = fields.Integer('Nombre de Borne', compute='_compute_asset_nbr', store=True)
    assignment_id = fields.Many2one('partner.asset.assignment', string="Borne")
    # model_asset = fields.Many2one(related='assignment_id.asset_model', store=True)
    asset_ids = fields.Many2many('partner.asset', compute="_compute_asset_ids",store=True)
    
    commission = fields.Float(string='Commission')

    contract_ids = fields.One2many('partner.contract', 'partner_id', string='Contracts')

    
    def button_asset_upgrade(self):
        for rec in self:
            if rec.assignment_ids:
                rec.assignment_id = rec.assignment_ids[0]
                rec.commission = rec.active_contract_id.commission_percentage

    
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



class PartnerContract(models.Model):
    _name = 'partner.contract'
    _description = 'Contract for a customer'

    name = fields.Char(string='Intitulé du contrat', required=True)
    partner_id = fields.Many2one('res.partner', string='Client')
    commission_percentage = fields.Float(string='Commission')
    start_date = fields.Date(string='Date Début')
    end_date = fields.Date(string='Date Fin')
    payment_terms = fields.Selection([
        ('net', 'Net'),
        ('15_days', '15 Jours'),
        ('30_days', '30 Jours'),
        ('45_days', '45 Jours')
    ], string='Modalités de paiement')
    contract_type = fields.Selection([
        ('maintenance', 'Maintenance'),
        ('service', 'Service'),
        ('asset', 'Borne')
    ], string='Type Contract')

