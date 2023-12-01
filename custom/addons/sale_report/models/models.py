# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from num2words import num2words
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def _num_to_words(self, num):
        def _num2words(number, lang):
            try:
                return num2words(number, lang=lang).title()
            except NotImplementedError:
                return num2words(number, lang='en').title()

        if num2words is None:
            return ""
        lang_code = self.env.context.get('lang') or self.env.user.lang
        lang = self.env['res.lang'].with_context(active_test=False).search([('code', '=', lang_code)])
        num_to_word = _num2words(num, lang=lang.iso_code)
        return num_to_word

    police = fields.Integer(string='Police des rapport', default=10)
    # customer_reference=fields.Char(string='Ref. Commande Client')
    # signataire_facture=fields.Many2one('res.users', string='Signataire')
    # invoice_object=fields.Char(string='Objet :')
    # source_document=fields.Char(string='N° Bon de commande :')
    amount_to_word = fields.Char(string="Montant en lettre:", compute='_compute_amount_to_word')

    # payment_mode = fields.Selection([('espece', 'Espèce'), ('cheque', 'Chèque'), ('virement', 'Virement'), ('traite', 'Traite')], 'Mode de Paiement', default="cheque")
    # discount_amount = fields.Monetary(string="Total Remise", compute="_compute_amount_discount", store=True)

    # @api.depends('invoice_line_ids.price_unit', 'invoice_line_ids.quantity', 'invoice_line_ids.price_subtotal')
    # def _compute_amount_discount(self):
    #     for rec in self:
    #         discount = 0
    #         for line in rec.invoice_line_ids:
    #             discount += line.price_unit * line.quantity - line.price_subtotal
    #         rec.discount_amount = discount



    def _compute_amount_to_word(self):
        for rec in self:
            rec.amount_to_word = str(self._num_to_words(rec.amount_total)).upper()

    def get_aggregated_invoice_lines(self):
        product_summary = {}

        for line in self.order_line:
            if not line.display_type:
                line_key = f"{line.product_id.id}"

                if line_key in product_summary:

                    product_summary[line_key]['price_unit'] = line.price_unit
                    product_summary[line_key]['discount'] = line.discount
                    product_summary[line_key]['quantity'] += line.product_uom_qty
                    product_summary[line_key]['subtotal'] += line.price_subtotal
                    product_summary[line_key]['tax_ids'] |= line.tax_id
                    product_summary[line_key]['amount_discount'] += (line.product_uom_qty * line.price_unit * line.discount) / 100
                else:
                    product_summary[line_key] = {
                        'image': line.product_id.image_1920,
                        'name': line.name,
                        'quantity': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'discount': line.discount,
                        'subtotal': line.price_subtotal,
                        'tax_ids': line.tax_id,
                        'amount_discount':(line.product_uom_qty * line.price_unit * line.discount) / 100,
                    }

        return product_summary

    def print_sale_report(self):
        self.ensure_one()

        report = self.env.ref('sale_report.action_report_saleorder_syht')
        report_vals = report.render_qweb_pdf(self.id)

        return self.env['ir.actions.report'].get_pdf([self.id], report.report_name, data=report_vals)


    # @api.depends('order_line.price_total')
    # def _amount_all(self):
    #     """
    #     Compute the total amounts of the SO.
    #     """
    #     for order in self:
    #         amount_untaxed = amount_tax = 0.0
    #         for line in order.order_line:
    #             amount_untaxed += line.price_subtotal
    #             amount_tax += line.price_tax
    #         order.update({
    #             'amount_untaxed': amount_untaxed,
    #             'amount_tax': amount_tax,
    #             'amount_total': amount_untaxed + amount_tax,
    #         })


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    price_total_excl_discount = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    # amount_discount = fields.Monetary(compute='_compute_amount', string='Remise', store=True)
    # #
    # @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    # def _compute_amount(self):
    #     """
    #     Compute the amounts of the SO line.
    #     """
    #     for line in self:
    #         price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
    #         taxes_excl_discount = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
    #                                         product=line.product_id, partner=line.order_id.partner_shipping_id)
    #         taxes = line.tax_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
    #         amount_discount = (line.product_uom_qty * line.price_unit * line.discount) / 100
    #         line.update({
    #             'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
    #             'price_total': taxes['total_included'],
    #             'price_total_excl_discount':taxes_excl_discount['total_included'],
    #             'amount_discount' : amount_discount,
    #             'price_subtotal': taxes['total_excluded'],
    #         })