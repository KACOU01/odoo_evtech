# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

try:
   import qrcode
except ImportError:
   qrcode = None
try:
   import base64
except ImportError:
   base64 = None
from io import BytesIO


_ASSET_STATE = [('new', 'Neuf'), ('used', 'Reconditionné')]

class PartnerAsset(models.Model):
    _name = 'partner.asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Partner asset description"
    
    name = fields.Char(string='Reference', tracking=True,)
    description = fields.Html("Description", help="Add a note about this asset",tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    company_id = fields.Many2one('res.company', 'Company',  default=lambda self: self.env.company, readonly=True, required=True,tracking=True,)
    acquisition_date = fields.Date(string="Date d'acquisition")
    first_assignment_date = fields.Date()
    # asset_model = fields.Many2one('partner.asset.model', string='Modele', tracking=True)
    asset_type = fields.Selection(selection=[('type_1', 'Type 1'), ('type_2', 'Type 2')])
    asset_id = fields.Char('N° de série', tracking=True,)
    quantity = fields.Float(string='Qté Compté',tracking=True,)
    qty_point_charge = fields.Float(string='Nombre de point',)
    qr_code = fields.Binary('QRcode', compute="_generate_qr")
    state = fields.Selection(selection=_ASSET_STATE, string="Etat")
    state_id = fields.Many2one('partner.asset.state', string="Status", tracking=True)
    is_assign = fields.Boolean(default=False, compute='_compute_is_assign', store=True, tracking=True)
    price = fields.Float("Prix",tracking=True)
    assignment_id = fields.Many2one('partner.asset.assignment', string="N° d'affectation",tracking=True)
    
    assignment_date = fields.Date(help="First assignment date",tracking=True)
    
    partner_id = fields.Many2one('res.partner', related='assignment_id.partner_id', string='Client', store=True,tracking=True)
    prix_par_kWh = fields.Float(string='Prix par kWh')
    assign_gestion_id = fields.Many2one('partner.asset.company', string="N° d'affectation",tracking=True)
    assignment_date_entreprise = fields.Date(help="First assignment date",tracking=True)
    entreprise_id = fields.Many2one('partner.entreprise', related='assign_gestion_id.entreprise_id', string='Entreprise', store=True,tracking=True)
    
    latitude_partner = fields.Float(string='Geo Latitude', digits=(10, 7), related='assignment_id.latitude')
    longitude_partner = fields.Float(string='Geo Longitude', digits=(10, 7), related='assignment_id.longitude')

    latitude_company = fields.Float(string='Geo Latitude', digits=(10, 7),related='assign_gestion_id.latitude')
    longitude_company = fields.Float(string='Geo Longitude', digits=(10, 7),related='assign_gestion_id.longitude')

    assign_partner_ids = fields.One2many('partner.asset.assignment', 'asset_id' , string='Assigne des bornes aux clients',tracking=True)
    assign_company_ids = fields.One2many('partner.asset.company', 'asset_id' , string='Assigne des bornes aux gestionnaires',tracking=True)

    sale_order_ids = fields.One2many('sale.order', 'asset_model', string='Devis',tracking=True)

    contract_id = fields.Many2one('partner.contract', string='Contract')

    services = fields.Many2many('partner.subs.type', string='Services',tracking=True)
    product_id = fields.Many2one('product.template', string="Produit")
    product_qty_available = fields.Float(related='product_id.qty_available', string="Qté en Stock")
    is_asset = fields.Boolean(string="Est une Borne", default=False)
    image = fields.Binary()

    def open_create_sale_order_wizard(self):
        return {
            'name': _('Create Sale Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'create.sale.order.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_asset_id': self.id},
        }

    # @api.onchange('asset_model', 'asset_id')
    # def _onchange_asset_fields(self):
    #     if self.asset_model and self.asset_id:
    #         self.name = f"{self.asset_model.name} - {self.asset_id}"

    @api.depends('assignment_id')
    def _compute_is_assign(self):
        for rec in self:
            if rec.assignment_id:
                rec.is_assign = True
            else:
                rec.is_assign = False
    
    
    _sql_constraints = [('partner_asset_name_unique', 'unique(name)', 'reference name already exists')]

    def liberez_asset(self):
        for rec in self:
            if rec.assignment_id:
                rec.assignment_id.action_do_cancel()
    
    def liberez_asset_entreprise(self):
        for rec in self:
            if rec.assign_gestion_id:
                rec.assign_gestion_id.action_do_cancel()
    
    def _generate_qr(self):
       "method to generate QR code"
       for rec in self:
           if qrcode and base64:
               qr = qrcode.QRCode(
                   version=1,
                   error_correction=qrcode.constants.ERROR_CORRECT_L,
                   box_size=3,
                   border=4,
               )
               qr.add_data("ID : ")
               qr.add_data(rec.asset_id)
               qr.add_data(", Model : ")
               qr.add_data(rec.asset_model.name)
               qr.make(fit=True)
               img = qr.make_image()
               temp = BytesIO()
               img.save(temp, format="PNG")
               qr_image = base64.b64encode(temp.getvalue())
               rec.update({'qr_code':qr_image})
           else:
               raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))
    
    @api.model
    def create(self, vals):
        res = super(PartnerAsset, self).create(vals)
        res.generate_product_template()
        return res


    def write(self, vals):
        res = super(PartnerAsset, self).write(vals)
        self.generate_product_template()
        return res

    def update_quantity(self):
        current_company = self.env['res.company'].browse(self.env.company.id)
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_id.product_variant_id.id),
            ('location_id', '=', warehouse.lot_stock_id.id),
            # ('lot_id', '=', lot.id),
            ('company_id', '=', self.company_id.id),
        ], limit=1)

        # Si l'enregistrement stock.quant n'existe pas, le créer avec la quantité du lot
        if not quant:
            quant = self.env['stock.quant'].create({
                'location_id': warehouse.lot_stock_id.id,
                'product_id': self.product_id.product_variant_id.id,

                'quantity': self.quantity,
                'company_id': self.company_id.id,
            })

        # Si l'enregistrement stock.quant existe, mettre à jour sa quantité avec la quantité du lot
        else:
            quant.quantity = self.quantity

        self.quantity = 0.0
    def generate_product_template(self):
        product_template = self.env['product.template'].search([('name', '=', self.name)], limit=1)
        if not product_template:
            if not self.product_id:
                product_template = self.env['product.template'].sudo().create({
                    'name': self.name,
                    'is_asset':self.is_asset,
                    'detailed_type':'product',
                    'type_product':'produit',
                    'list_price':self.price,
                    'image_1920':self.image,
                    # 'taxes_id':False,
                    # Set other fields of product template based on asset model attributes
                })
                product_product = self.env['product.product'].search([('name', '=', self.name),('product_tmpl_id','=',product_template.id)], limit=1)
                product_product.sudo().write({
                        'is_asset': self.is_asset,
                        'list_price': self.price,
                    'type_product': 'produit',
                    'image_1920':self.image,
                        # 'taxes_id': False,
                        # Set other fields of product template based on asset model attributes
                    })
                self.product_id = product_template.id
                # current_company = self.env['res.company'].browse(self.env.company.id)
                # warehouse = self.env['stock.warehouse'].search([], limit=1)
                # quant = self.env['stock.quant'].search([
                #     ('product_id', '=', product_template.product_variant_id.id),
                #     ('location_id', '=', warehouse.lot_stock_id.id),
                #     # ('lot_id', '=', lot.id),
                #     ('company_id', '=', current_company.id),
                # ], limit=1)
                #
                # # Si l'enregistrement stock.quant n'existe pas, le créer avec la quantité du lot
                # if not quant:
                #     quant = self.env['stock.quant'].sudo().create({
                #         'product_id': product_template.product_variant_id.id,
                #         'location_id': warehouse.lot_stock_id.id,
                #         'quantity': self.quantity,
                #         'company_id': self.env.company.id,
                #     })
                #
                # # Si l'enregistrement stock.quant existe, mettre à jour sa quantité avec la quantité du lot
                # else:
                #     pass
                    # quant.quantity = quant.quantity + 1
            else:
                product_template = self.env['product.template'].search([('id', '=', self.product_id.id)], limit=1)
                product_template.sudo().write({
                    'name': self.name,
                    # 'taxes_id': False,
                    'list_price': self.price,
                    'type_product': 'produit',
                    'image_1920':self.image,
                    # Set other fields of product template based on asset model attributes
                })

            # Open the product.template in edit mode
            return {
                'name': 'Product Template',
                'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'res_id': product_template.id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
            }
        else:
            product_template = self.env['product.template'].search([('id', '=', self.product_id.id)], limit=1)
            product_template.sudo().write({
                'name': self.name,
                # 'taxes_id': False,
                'list_price': self.price,
                'type_product': 'produit',
                'image_1920':self.image,
                # Set other fields of product template based on asset model attributes
            })
            product_product = self.env['product.product'].search(
                [('name', '=', self.name), ('product_tmpl_id', '=', product_template.id)], limit=1)
            product_product.sudo().write({
                'is_asset': self.is_asset,
                'type_product': 'produit',
                'list_price': self.price,
                'image_1920':self.image,
                # 'taxes_id': False,
                # Set other fields of product template based on asset model attributes
            })
            # Product template already exists, raise a validation error
            return {
                'name': 'Product Template',
                'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'res_id': product_template.id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
            }

            # raise ValidationError('Article %s existe' % self.name)