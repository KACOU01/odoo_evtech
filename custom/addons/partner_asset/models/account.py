from odoo import models, fields, api, _

from datetime import timedelta
from dateutil.relativedelta import relativedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

    number_invoice = fields.Char(string='Numero Facture', store=True)
    amount_paid = fields.Monetary(compute="_compute_amount_paid", store=True, string="Montant Payé")

    def _compute_amount_paid(self):
        for move in self:
            move.amount_paid = move.amount_total - move.amount_residual

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    date_debut = fields.Date(string="Date de début", invisible=True,compute='_compute_date',store=True)
    duree_en_mois = fields.Integer(string="Durée (mois)", invisible=True,compute='_compute_date',store=True)
    date_fin = fields.Date(string="Date de fin", store=True)
    is_maintenance = fields.Char(string="Est un abonnement", store=True)
    lot_number = fields.Char(string='Numero serie', readonly=True, compute='_compute_serie_number', store=True)

    @api.onchange('serie_number')
    def _onchange_serie_number(self):
        for line in self:
            order_line = line.sale_line_ids
            if order_line:
                line.lot_number = order_line[0].serie_number


    @api.depends('date_debut', 'duree_en_mois')
    def _compute_date_fin(self):
        for picking in self:
            if picking.date_debut and picking.duree_en_mois:
                picking.date_fin = picking.date_debut + relativedelta(months=picking.duree_en_mois)
            else:
                picking.date_fin = False

    @api.depends('sale_line_ids')
    def _compute_serie_number(self):
        for line in self:
            order_line = line.sale_line_ids
            if order_line:
                line.lot_number = order_line[0].serie_number


    @api.depends('sale_line_ids')
    def _compute_date(self):
        for line in self:
            order_line = line.sale_line_ids
            if order_line:
                line.date_debut = order_line[0].date_debut
                line.duree_en_mois = order_line[0].duree_en_mois
                line.date_fin = order_line[0].date_fin
                line.is_maintenance = order_line[0].is_maintenance
