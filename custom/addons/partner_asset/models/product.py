# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    is_asset = fields.Boolean(string="Est une Borne", default=False)
    type_service = fields.Selection(selection=[('maintenance', 'Maintenance'), ('installation', 'Installation'),('other','Autre')])

    type_product = fields.Selection(selection=[('produit', 'Produit'), ('service', 'Service')],
                                    store=True, string='Type Product')

    # asset_id = fields.Many2one('partner.asset', string='Borner', tracking=True)

    @api.model
    def create(self, vals):
        product = super(ProductTemplate, self).create(vals)
        # search_product = self.env['partner.subs.type'].search([('name','=',product.name)])
        # if not search_product:
        #     if product.detailed_type == 'service':
        #         self.env['partner.subs.type'].create({
        #             'name': product.name,
        #             'description':product.name,
        #             'active': True,
        #         })
        search_product = self.env['partner.asset'].search([('name', '=', product.name)])
        if not search_product:
            if product.is_asset == True:
                self.env['partner.asset'].create({
                    'name': product.name,
                    'price': product.list_price,
                    'active': True,
                })
        return product

class ProductProduct(models.Model):
    _inherit = "product.product"

    
    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     if args is None:
    #         args = []
    #     args.append(('qty_available', '>=', 1))
    #     return super(ProductProduct, self).search(args, offset, limit, order, count)

    type_product = fields.Selection(selection=[('produit', 'Produit'), ('service', 'Service')], compute='_compute_product', store=True, inverse='_set_type_product',string='Type Product', default='produit')
    is_asset = fields.Boolean(string="Est une Borne", default=False,compute='_compute_is_asset',store=True,inverse='_set_is_asset')
    # asset_id = fields.Many2one('partner.asset', string='Borne', tracking=True)
    type_service = fields.Selection(selection=[('maintenance', 'Maintenance'), ('installation', 'Installation'),('other','Autre')])



    def _compute_is_asset(self):
        """Get the is_asset value from the template if no value is set on the variant."""
        for record in self:
            record.is_asset = record.product_tmpl_id.is_asset

    def _set_is_asset(self):
        for record in self:
            record.product_tmpl_id.is_asset = record.is_asset

    def _compute_product(self):
        """Get the is_asset value from the template if no value is set on the variant."""
        for record in self:
            record.type_product = record.product_tmpl_id.type_product

    def _set_type_product(self):
        for record in self:
            record.product_tmpl_id.type_product = record.type_product
