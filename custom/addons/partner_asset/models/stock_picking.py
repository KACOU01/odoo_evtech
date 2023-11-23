from odoo import models, fields, api

from datetime import timedelta
from dateutil.relativedelta import relativedelta


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.constrains('move_line_ids.number_serie',)
    def check_unique_serial_numbers(self):
        unique_serial_numbers = set()

        for move_line in self.move_line_ids:
            if move_line.number_serie:
                if move_line.number_serie in unique_serial_numbers:
                    # Si le numéro de série est en double, vous pouvez effectuer une action ici
                    # Par exemple, lever une exception, afficher un avertissement, etc.
                    raise ValidationError("Le numéro de série '{}' est en double.".format(move_line.number_serie))
                else:
                    unique_serial_numbers.add(move_line.number_serie)


    def button_validate(self):
        res = super(StockPicking, self).button_validate()

        # Call the update_sale_order_line function for each move_line in the picking
        for move_line in self.move_line_ids:
            move_line.update_sale_order_line()

        return res
    def button_validate(self):
        result = super(StockPicking, self).button_validate()
        self._create_asset_assignments()
        for move_line in self.move_line_ids:
            move_line.update_sale_order_line()
            # move_line._create_asset_assignments()
        return result

    def _create_partner_subscriptions(self):
        for move_line in self.move_line_ids:
            if move_line.product_id.detailed_type == 'service':
                subs_type_service = self.env['partner.subs.type'].search([('name', '=', move_line.product_id.product_tmpl_id.name)], limit=1)
                subscription = self.env['partner.subscription'].create({
                    'name': '/',
                    'company_id': self.company_id.id,
                    # 'amount': move_line.price_subtotal,
                    'first_date': self.date_debut,
                    'end_date': self.date_fin,
                    'type': subs_type_service.id,
                    'state': 'confirm',
                    'partner_id': self.partner_id.id,
                })


    # def action_done(self):
    #     result = super(StockPicking, self).action_done()
    #     self._create_asset_assignments()
    #     return result

    def _create_asset_assignments(self):
        for move_line in self.move_line_ids.filtered(lambda line: line.product_id.is_asset):
            aseet = self.env['partner.asset'].search([('name', '=', move_line.product_id.product_tmpl_id.name)], limit=1)
            assignment = self.env['partner.asset.company'].sudo().create({
                'name': self.env["ir.sequence"].next_by_code("assignment.code") or '/',
                'asset_id': aseet.id,
                'entreprise_id': move_line.entreprise_id.id,
                'lot_number':move_line.number_serie,
            })

            # assignment.action_validate()


class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_ids = fields.Many2many(default=False,domain="[('product_id', '=', product_id), ('company_id', '=', company_id),('quant_ids.quantity', '>', 0),('quant_ids.location_id','=',location_id)]")
    date_debut = fields.Date(string="Date de début")
    duree_en_mois = fields.Integer(string="Durée (mois)")
    date_fin = fields.Date(string="Date de fin", compute='_compute_date_fin', store=True)
    is_maintenance = fields.Boolean(string="Est un abonnement", compute='_compute_is_subscription', store=True,default=True)

    @api.depends('product_id', 'product_id.name')
    def _compute_is_subscription(self):
        abonnement_keywords = ['Abonnement', 'Maintenance']  # Liste des mots-clés pour les produits d'abonnement
        for picking in self:
            picking.is_maintenance = any(keyword in picking.product_id.name for keyword in abonnement_keywords)

    @api.depends('date_debut', 'duree_en_mois')
    def _compute_date_fin(self):
        for picking in self:
            if picking.date_debut and picking.duree_en_mois:
                picking.date_fin = picking.date_debut + relativedelta(months=picking.duree_en_mois)
            else:
                picking.date_fin = False

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    _order = 'product_id desc'

    entreprise_id = fields.Many2one('partner.entreprise', string='Entreprise', tracking=True)
    date_debut = fields.Date(string="Date de début")
    duree_en_mois = fields.Integer(string="Durée (mois)")
    date_fin = fields.Date(string="Date de fin", compute='_compute_date_fin', store=True)
    is_maintenance = fields.Selection(
        selection=[('maintenance', 'Maintenance'), ('installation', 'Installation'), ('other', 'Autre')],related='product_id.type_service', store=True,)
    # is_maintenance = fields.Char(string="Est un abonnement", related='product_id.type_service', store=True,)
    is_asset = fields.Boolean(string="Est un abonnement", related='product_id.is_asset', store=True,default=True)

    lot_id = fields.Many2one(
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id), ('quant_ids.quantity', '>', 0), ('quant_ids.location_id', '=', location_id)]"
    )
    number_serie = fields.Char('N° de série', tracking=True)

    _sql_constraints = [
        ('uniq_number_serie', 'unique (number_serie)', 'Numero de Serie est Unique!')
    ]


    @api.model
    def create(self, vals):
        move = super(StockMoveLine, self).create(vals)
        # Empty the lot_id field when creating a new record
        vals['lot_id'] = False
        return move

    def write(self, vals):
        # Empty the lot_id field when creating or updating a record
        if vals.get('product_id') or vals.get('company_id') or vals.get('location_id'):
            vals['lot_id'] = False
        return super(StockMoveLine, self).write(vals)

    @api.model
    def _default_lot_id(self):
        return None # Renvoyer l'ID actuel si ce n'est pas une création.
        
    def update_sale_order_line(self):
        for rs in self:
            if rs.move_id.sale_line_id and rs.number_serie:
                serie_number = rs.move_id.sale_line_id.serie_number
                new_serie_number = rs.number_serie

                if serie_number and new_serie_number:
                    if new_serie_number not in serie_number:
                        updated_serie_number = f"{serie_number}; {new_serie_number}"
                    else:
                        updated_serie_number = serie_number
                elif new_serie_number:
                    updated_serie_number = new_serie_number
                else:
                    updated_serie_number = serie_number

                rs.move_id.sale_line_id.write({'serie_number': updated_serie_number})

            if rs.move_id.sale_line_id and rs.date_debut:
                rs.move_id.sale_line_id.write({'date_debut': rs.date_debut,'duree_en_mois':rs.duree_en_mois,
                                               'date_fin':rs.date_fin,
                                               'is_maintenance':rs.is_maintenance})

    # @api.depends('product_id', 'product_id.name')
    # def _compute_is_subscription(self):
    #     abonnement_keywords = ['Abonnement', 'Maintenance']  # Liste des mots-clés pour les produits d'abonnement
    #     for picking in self:
    #         picking.is_maintenance = any(keyword in picking.product_id.name for keyword in abonnement_keywords)
    #

    @api.depends('date_debut', 'duree_en_mois')
    def _compute_date_fin(self):
        for picking in self:
            if picking.date_debut and picking.duree_en_mois:
                picking.date_fin = picking.date_debut + relativedelta(months=picking.duree_en_mois)
            else:
                picking.date_fin = False

class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    company_id = fields.Many2one('res.company', 'Company', required=True, store=True, index=True,
                                 default=lambda self: self.env.company.id)

    @api.model
    def create(self, vals):
        lot = super(StockProductionLot, self).create(vals)

        if lot.product_id:
            # Récupérer l'emplacement principal du premier entrepôt
            warehouse = self.env['stock.warehouse'].search([], limit=1)
            if warehouse and warehouse.lot_stock_id:
                # Rechercher l'enregistrement stock.quant correspondant pour le produit, l'emplacement principal et le lot
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', lot.product_id.id),
                    ('location_id', '=', warehouse.lot_stock_id.id),
                    ('lot_id', '=', lot.id),
                    ('company_id', '=', lot.company_id.id),
                ], limit=1)

                # Si l'enregistrement stock.quant n'existe pas, le créer avec la quantité du lot
                if not quant:
                    quant = self.env['stock.quant'].create({
                        'product_id': lot.product_id.id,
                        'location_id': warehouse.lot_stock_id.id,
                        'lot_id': lot.id,
                        'quantity': 1,
                        'company_id': lot.company_id.id,
                    })

                # Si l'enregistrement stock.quant existe, mettre à jour sa quantité avec la quantité du lot
                else:
                    quant.quantity = quant.quantity + 1

        return lot


# Assuming you have already imported necessary modules and defined the stock.move.line model.

# class StockMoveLine(models.Model):
#     _inherit = 'stock.move.line'






# # Assuming you have already imported necessary modules and defined the stock.move model.

# class StockMove(models.Model):
#     _inherit = 'stock.move'

#     lot_ids = fields.Many2many(default=False,domain="[('product_id', '=', product_id), ('company_id', '=', company_id),('quant_ids.quantity', '>', 0),('quant_ids.location_id','=',location_id)]")


#     def _default_lot_ids(self):
#         return [(5, 0, 0)]  # This will return an empty list, setting the field to empty by default.
