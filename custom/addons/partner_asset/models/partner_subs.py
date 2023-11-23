# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO

_ASSET_STATE = [('draft', 'Brouillons'), ('confirm', 'Confimer'), ('expire', 'Expire'), ('cancel', 'Annuler')]


class PartnerSubs(models.Model):
    _name = 'partner.subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Partner subscription"

    @api.model
    def _get_default_name(self):
        return self.env["ir.sequence"].next_by_code("subscript.code")

    name = fields.Char(required=True, default='/', tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, tracking=True,
                                 readonly=True, required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(currency_field='currency_id', store=True, string="Montant", tracking=True)
    first_date = fields.Date(string="Date de debut")
    end_date = fields.Date(string="Date de debut")
    # asset_model_id = fields.Many2one('partner.asset.model', string='Modele de Borne', tracking=True)
    asset_id = fields.Many2one('partner.asset', string='Borne', tracking=True)

    type = fields.Many2one('type.subscription', string='Type', tracking=True)

    state = fields.Selection(selection=_ASSET_STATE, string="Etat", tracking=True)
    partner_id = fields.Many2one('res.partner', related='asset_id.partner_id', string='Client', store=True,
                                 tracking=True)

    days_expire = fields.Integer(string="Jours intervalle")

    @api.depends('end_date')
    def _compute_days_expire(self):
        today = fields.Date.today()
        for subscription in self:
            if subscription.end_date:
                end_date = fields.Datetime.from_string(subscription.end_date)
                days_diff = (end_date - today).days
                subscription.days_expire = days_diff

                if days_diff < 0:
                    subscription.state = 'expire'
            else:
                subscription.days_expire = 0

    # _sql_constraints = [('partner_asset_name_unique', 'unique(name)', 'reference name already exists')]

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(with_company=vals['company_id']).next_by_code(
                'subscript.code') or '/'
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('subscript.code') or '/'
        res = super(PartnerSubs, self).create(vals)
        return res

    def write(self, vals):
        res = super(PartnerSubs, self).write(vals)
        return res

    def unlink(self):
        # if self.state in ('done'):
        #    raise ValidationError(_('Vous ne pouvez pas supprimer une assignation déja validée'))
        # self.asset_id.unlink()
        return super(PartnerSubs, self).unlink()


class SubsType(models.Model):
    _name = 'type.subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Type Abonnement"

    name = fields.Char()
    description = fields.Html("Description", help="Description du type abonnement", tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    price = fields.Float("Prix", tracking=True)
    product_id = fields.Many2one('product.template', string="Produit")
    image = fields.Binary()

    @api.model
    def create(self, vals):
        res = super(SubsType, self).create(vals)
        res.generate_product_template()
        return res

    def write(self, vals):
        res = super(SubsType, self).write(vals)
        self.generate_product_template()
        return res

    def generate_product_template(self):
        product_template = self.env['product.template'].search([('name', '=', self.name)], limit=1)
        if not product_template:
            product_template = self.env['product.template'].sudo().create({
                'name': self.name,
                'detailed_type': 'product',
                'type_product': 'service',
                'image_1920':self.image,
                # 'list_price':self.price,
                # 'taxes_id': False,
                # Set other fields of product template based on asset model attributes
            })
            product_product = self.env['product.product'].search(
                [('name', '=', self.name), ('product_tmpl_id', '=', product_template.id)], limit=1)
            product_product.sudo().write({
                'list_price': self.price,
                # 'taxes_id': False,
                'detailed_type': 'product',
                'type_product': 'service',
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
                'type_product': 'service',
            }
        else:
            product_product = self.env['product.product'].search(
                [('name', '=', self.name), ('product_tmpl_id', '=', product_template.id)], limit=1)
            product_product.sudo().write({
                'list_price': self.price,
                # 'taxes_id': False,
                'detailed_type': 'product',
                'type_product': 'service',
                'image_1920':self.image,
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


class PartnerSubsType(models.Model):
    _name = 'partner.subs.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Serice/Maintenance"

    name = fields.Char()
    description = fields.Html("Description", help="Description Service", tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    price = fields.Float("Prix", tracking=True)
    product_id = fields.Many2one('product.template', string="Produit")
    type_service = fields.Selection(selection=[('maintenance', 'Maintenance'), ('installation', 'Installation'),('other','Autre')])
    image = fields.Binary()

    @api.model
    def create(self, vals):
        res = super(PartnerSubsType, self).create(vals)
        res.generate_product_template()
        return res

    def write(self, vals):
        res = super(PartnerSubsType, self).write(vals)
        self.generate_product_template()
        return res

    def update_quantity(self,product_id):
        current_company = self.env['res.company'].browse(self.env.company.id)
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        quant = self.env['stock.quant'].search([
            ('product_id', '=', product_id),
            ('location_id', '=', warehouse.lot_stock_id.id),
            # ('lot_id', '=', lot.id),
            ('company_id', '=', current_company.id),
        ], limit=1)

        # Si l'enregistrement stock.quant n'existe pas, le créer avec la quantité du lot
        if not quant:
            quant = self.env['stock.quant'].create({
                'product_id': product_id,
                'location_id': warehouse.lot_stock_id.id,
                'quantity': 8000000000,
                'company_id': self.env.company.id,
            })

        # Si l'enregistrement stock.quant existe, mettre à jour sa quantité avec la quantité du lot
        else:
            quant.quantity = quant.quantity + 1

    def generate_product_template(self):
        product_template = self.env['product.template'].search([('name', '=', self.name)], limit=1)
        if not product_template:
            if self.product_id:
                product_template = self.env['product.template'].search([('id', '=', self.product_id.id)], limit=1)
                product_template.sudo().write({
                    'name': self.name,
                    # 'taxes_id': False,
                    'list_price': self.price,
                    'detailed_type': 'product',
                    'type_product': 'service',
                    'type_service':self.type_service,
                    'image_1920':self.image,
                    # Set other fields of product template based on asset model attributes
                })
                product_product = self.env['product.product'].search(
                    [('name', '=', self.name), ('product_tmpl_id', '=', product_template.id)], limit=1)
                product_product.sudo().write({
                    # 'list_price': self.price,
                    # 'taxes_id': False,
                    # 'detailed_type': 'product',
                    'type_product': 'service',
                    'type_service': self.type_service,
                    'image_1920':self.image,
                })
            else:
                product_template = self.env['product.template'].sudo().create({
                    'name': self.name,
                    'detailed_type': 'product',
                    'type_product': 'service',
                    'list_price': self.price,
                    'type_service':self.type_service,
                    'image_1920':self.image,
                    # 'taxes_id': False,
                })
                product_product = self.env['product.product'].search(
                    [('name', '=', self.name), ('product_tmpl_id', '=', product_template.id)], limit=1)
                product_product.sudo().write({
                    # 'list_price': self.price,
                    # 'taxes_id': False,
                    'detailed_type': 'product',
                    'type_product': 'service',
                    'type_service':self.type_service,
                    'image_1920':self.image,
                })
                self.product_id = product_template.id
                # Open the product.template in edit mode
            self.update_quantity(self.product_id.product_variant_id.id)

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
            if self.product_id:
                product_template = self.env['product.template'].search([('id', '=', self.product_id.id)], limit=1)
                product_template.sudo().write({
                    'name': self.name,
                    # 'taxes_id': False,
                    'list_price': self.price,
                    # 'detailed_type': 'product',
                    'type_product': 'service',
                    'type_service':self.type_service,
                    'image_1920':self.image,
                    # Set other fields of product template based on asset model attributes
                })
                product_product = self.env['product.product'].search(
                    [('name', '=', self.name), ('product_tmpl_id', '=', product_template.id)], limit=1)
                product_product.sudo().write({
                    # 'list_price': self.price,
                    # 'taxes_id': False,
                    # 'detailed_type': 'product',
                    'type_product': 'service',
                    'type_service': self.type_service,
                    'image_1920':self.image,
                })
                self.update_quantity(self.product_id.product_variant_id.id)
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
