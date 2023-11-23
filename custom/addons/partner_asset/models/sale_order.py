# -*- coding: utf-8 -*-

from odoo import models, fields, api

from datetime import timedelta
from dateutil.relativedelta import relativedelta


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    date_debut = fields.Date(string="Date de début", invisible=True)
    duree_en_mois = fields.Integer(string="Durée (mois)", invisible=True)
    date_fin = fields.Date(string="Date de fin", store=True)
    serie_number = fields.Char(string='Numero serie', readonly=True)
    is_maintenance = fields.Char(string="Est un abonnement", store=True)

    @api.depends('product_id', 'product_id.name')
    def _compute_is_subscription(self):
        abonnement_keywords = ['Abonnement', 'Maintenance']  # Liste des mots-clés pour les produits d'abonnement
        for line in self:
            line.is_maintenance = any(keyword in line.product_id.name for keyword in abonnement_keywords)


    # def _is_abonnement_product(self):
    #     abonnement_keywords = ['abonnement']  # Liste des mots-clés pour les produits d'abonnement
    #     for line in self:
    #         if line.product_id.name and any(keyword in line.product_id.name.lower() for keyword in abonnement_keywords):
    #             return True
    #     return False

    def _compute_date_fin(self):
        for line in self:
            if line.duree_en_mois and line.date_debut:
                line.date_fin = line.date_debut + relativedelta(months=line.duree_en_mois)
            else:
                line.date_fin = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.order_id._create_additional_order_lines()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    comment = fields.Html("Commentaire", tracking=1)
    asset_model = fields.Many2one('partner.asset', string='Modèle de la borne')
    asset_serial_number = fields.Char(string='Numéro de série de la borne', related='asset_model.asset_id')
    partner_asset_ids = fields.Many2many('partner.asset', compute='_compute_partner_asset_ids', string='Borne')
    amount_invoiced = fields.Monetary(compute="_compute_amount_residual", store=True,string="Montant Facture")
    amount_residual = fields.Monetary(compute="_compute_amount_residual", store=True,string="Montant Restant")
    amount_paid = fields.Monetary(compute="_compute_amount_residual", store=True,string="Montant Payé")
    state_payment = fields.Selection(
        [('not_paid', 'Pas de Paiement'), ('in_payment', 'En Paiement'), ('paid', 'Payé'),('partial','Partiellement Reglé')],
        string='Etat Paiement',
        default='not_paid',
        compute='_compute_invoice_payment_states',
        help='Payment state of the order.'

    )

    state_invoice = fields.Selection(
        [('not_invoice','Pas de facture'),('draft', 'Broullion'), ('posted', 'Comptabilisé'), ('cancel', 'Annulé')],
        string='Etat Facture',
        default='not_invoice',
        compute='_compute_invoice_payment_states',
        help='Invoice state of the order.'
    )
    state = fields.Selection(selection_add=[('invoice_draft', 'Facture en attente de paiement'),('invoice_in_paid', 'Facture en paiement'),('invoice_paid','Payé')])
    @api.model
    def create(self, vals):
        records = super(SaleOrder, self).create(vals)
        for record in records:
            record._create_additional_order_lines()
        return records

    def write(self, vals):
        records = super(SaleOrder, self).write(vals)
        self._create_additional_order_lines()
        return records

    @api.depends('invoice_ids.amount_residual', 'invoice_ids.amount_total',)
    def _compute_amount_residual(self):
        for order in self:
            moves = order.invoice_ids.filtered(lambda m:m.state != 'cancel')
            if moves:
                order.amount_residual = sum([move.amount_residual for move in moves])
                order.amount_invoiced = sum([move.amount_total for move in moves])
                order.amount_paid = order.amount_invoiced - order.amount_residual
            else:
                order.amount_residual = 0
                order.amount_invoiced = 0
                order.amount_paid = 0

    @api.depends('invoice_ids.state','invoice_ids.payment_state',)
    def _compute_invoice_payment_states(self):
        for order in self:
            if order.invoice_ids:
                invoice_states = order.invoice_ids.mapped('state')
                payment_states = order.invoice_ids.mapped('payment_state')

                if 'draft' in invoice_states:
                    order.state_invoice = 'draft'
                elif 'posted' in invoice_states:
                    order.state_invoice = 'posted'
                elif 'cancel' in invoice_states:
                    order.state_invoice = 'cancel'
                else:
                    order.state_invoice = 'not_invoice'

                if 'not_paid' in payment_states:
                    order.state_payment = 'not_paid'
                    order.state = 'invoice_draft'
                elif 'in_payment' in payment_states:
                    order.state_payment = 'in_payment'
                    order.state = 'invoice_in_paid'
                elif 'paid' in payment_states:
                    order.state_payment = 'paid'
                    order.state = 'invoice_paid'
                elif 'partial' in payment_states:
                    order.state_payment = 'partial'
                    order.state = 'invoice_in_paid'
            else:
                order.state_invoice = 'not_invoice'
                order.state_payment = 'not_paid'
    @api.onchange('invoice_ids',)
    def _onchange_invoice_payment_ids(self):
        self._compute_invoice_payment_states()

    @api.depends('partner_id.asset_ids')
    def _compute_partner_asset_ids(self):
        for order in self:
            order.partner_asset_ids = order.partner_id.asset_ids
    
    # def _create_additional_order_lines(self):
    #     lines_to_create = []

    #     for order in self:
    #         existing_products = order.order_line.mapped('product_id.product_variant_id')
    #         new_lines = []

    #         for res in order.order_line:
    #             asset = self.env['partner.asset'].search([('name', '=', res.product_id.product_tmpl_id.name)], limit=1)
    #             for product_name in asset.services:
    #                 product = self.env['product.template'].search([('name', '=', product_name.name)], limit=1)
    #                 if product and product.product_variant_id not in existing_products:
    #                     quantity = int(res.product_uom_qty)  # Convertir en entier
    #                     for _ in range(quantity):
    #                         line_values = {
    #                             'product_id': product.product_variant_id.id,
    #                             'product_uom_qty': 1.0,
    #                             'name': product.product_variant_id.partner_ref,
    #                             'order_id': order.id,
    #                         }
    #                         new_lines.append((0, 0, line_values))

    #         # Supprimer toutes les lignes existantes
    #         order.order_line.unlink()

    #         # Recréer toutes les lignes, y compris les nouvelles
    #         lines_to_create.extend(new_lines)
    #         self.write({
    #             'order_line': lines_to_create
    #         })

    def _create_additional_order_lines(self):
        lines_to_create = []

        for order in self:
            existing_products = order.order_line.mapped('product_id.product_variant_id')
            for res in order.order_line:
                asset = self.env['partner.asset'].search([('name', '=', res.product_id.product_tmpl_id.name),('is_asset','=',True)], limit=1)
                quantity = int(res.product_uom_qty)  # Convertir en entier
                if asset:
                    for _ in range(quantity - 1):
                        line_values = {
                                'product_id': res.product_id.id,
                                'product_uom_qty': 1.0,
                                'name': res.product_id.partner_ref,
                                'order_id': order.id,
                        }
                        lines_to_create.append((0, 0, line_values))
                for product_name in asset.services:
                    product = self.env['product.template'].search([('name', '=', product_name.name)], limit=1)
                    if product and product.product_variant_id not in existing_products:
                        quantity = int(res.product_uom_qty)  # Convertir en entier
                        
                        for _ in range(quantity):
                            line_values = {
                                'product_id': product.product_variant_id.id,
                                'product_uom_qty': 1.0,
                                'name': product.product_variant_id.partner_ref,
                                'order_id': order.id,
                            }
                            lines_to_create.append((0, 0, line_values))
                if res.product_id.is_asset == True:
                    res.product_uom_qty = 1

        if lines_to_create:
            self.write({
                'order_line': lines_to_create
            })

    # def _prepare_stock_picking(self):
    #     res = super(SaleOrder, self)._prepare_stock_picking()
    #     picking_lines = []
    #
    #     for line in self.order_line:
    #         if line.product_id.detailed_type == 'service':
    #             # Créez une ligne de bon de livraison pour les services
    #             picking_line = {
    #                 'name': line.name,
    #                 'product_id': line.product_id.id,
    #                 'product_uom': line.product_uom.id,
    #                 'product_uom_qty': line.product_uom_qty,
    #                 # Ajoutez d'autres champs requis pour la ligne de bon de livraison
    #             }
    #             picking_lines.append((0, 0, picking_line))
    #
    #     res['move_ids_without_package'] = picking_lines
    #     return res