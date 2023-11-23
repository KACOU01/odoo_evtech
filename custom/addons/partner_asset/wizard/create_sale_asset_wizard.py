from odoo import models, fields, api
from odoo.exceptions import UserError

class CreateSaleOrderWizard(models.TransientModel):
    _name = 'create.sale.order.wizard'
    _description = 'Create Sale Order Wizard'

    partner_id = fields.Many2one('res.partner', string='Client', required=True)
    # contract_id = fields.Many2one('partner.contract', string='Contract', required=True)
    asset_id = fields.Many2one('partner.asset', string='Borne', required=True)
    service_ids = fields.Many2many('partner.subs.type', string='Services', related='asset_id.services')

    def create_sale_order(self):
        product = self.env['product.product'].search([('name','=',self.asset_id.name),('is_asset', '=', True)], limit=1)
        if product:

            sale_order = self.env['sale.order'].create({
                'partner_id': self.partner_id.id,
                'asset_model': self.asset_id.id,
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom_qty': 1,
                    'price_unit': product.list_price,
                })],
            })
            services = self.env['product.product'].search([
                ('name', 'in', self.service_ids.mapped('name')),
            ])
            order_lines = []
            for service in services:
                order_line = (0, 0, {
                    'product_id': service.id,
                    'name': service.name,
                    'product_uom_qty': 1,
                    'price_unit': service.list_price,
                })
                order_lines.append(order_line)

            sale_order.write({'order_line': order_lines})

            assignment = self.env['partner.asset.assignment'].sudo().create({
                'partner_id': self.partner_id.id,
                # 'contract_id': self.contract_id.id,
                'asset_id': self.asset_id.id,
                # 'state': 'done',
           
            })
            assignment.action_validate()
            # Ouvrir l'interface du devis nouvellement créé
            action = self.env.ref('sale.action_quotations').read()[0]
            action['res_id'] = sale_order.id
            return action
        else:
            raise UserError('No asset product found.')

