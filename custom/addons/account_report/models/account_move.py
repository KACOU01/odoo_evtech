# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from num2words import num2words
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    regime_fiscal = fields.Many2one('fiscal.regime', string="Regime Fiscal")


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _default_note(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'account.use_invoice_terms') and self.env.company.invoice_terms or ''

    # num2words convert number to word
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

    # delivery_slip=fields.Char(string='N° Bordereau de Livraison')
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

        for line in self.invoice_line_ids:
            if not line.display_type:
                line_key = f"{line.product_id.id}"

                if line_key in product_summary:
                    product_summary[line_key]['price_unit'] = line.price_unit
                    product_summary[line_key]['discount'] = line.discount
                    product_summary[line_key]['quantity'] += line.quantity
                    product_summary[line_key]['subtotal'] += line.price_subtotal
                    product_summary[line_key]['tax_ids'] |= line.tax_ids
                    product_summary[line_key]['amount_discount'] += (line.quantity * line.price_unit * line.discount) / 100
                else:
                    product_summary[line_key] = {
                        'image': line.product_id.image_1920,
                        'name': line.name,
                        'lot_number': line.lot_number,
                        'quantity': int(line.quantity),
                        'price_unit': line.price_unit,
                        'discount': line.discount,
                        'subtotal': line.price_subtotal,
                        'tax_ids': line.tax_ids,
                        'amount_discount': (line.quantity * line.price_unit * line.discount) / 100,
                    }

        return product_summary

    def print_invoice_report(self):
        self.ensure_one()

        report = self.env.ref('account.report_account_inherit')
        report_vals = report.render_qweb_pdf(self.id)

        return self.env['ir.actions.report'].get_pdf([self.id], report.report_name, data=report_vals)


# class AccountMoveLine(models.Model):
#     _inherit = "account.move.line"

#     acompte = fields.Boolean(default=False)

#
class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    amount_discount = fields.Monetary(string='Remise Montant', store=True, readonly=True,
                                      currency_field='currency_id')

#     @api.model
#     def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
#                                             move_type):
#         ''' This method is used to compute 'price_total' & 'price_subtotal'.
#
#         :param price_unit:  The current price unit.
#         :param quantity:    The current quantity.
#         :param discount:    The current discount.
#         :param currency:    The line's currency.
#         :param product:     The line's product.
#         :param partner:     The line's partner.
#         :param taxes:       The applied taxes.
#         :param move_type:   The type of the move.
#         :return:            A dictionary containing 'price_subtotal' & 'price_total'.
#         '''
#         res = {}
#
#         # Compute 'price_subtotal'.
#         line_discount_price_unit = price_unit * (1 - (discount / 100.0))
#         subtotal = quantity * price_unit
#         amount_discount = (quantity * price_unit * discount) / 100
#
#         # Compute 'price_total'.
#         if taxes:
#             taxes_res = taxes._origin.with_context(force_sign=1).compute_all(price_unit,
#                                                                              quantity=quantity, currency=currency,
#                                                                              product=product, partner=partner,
#                                                                              is_refund=move_type in (
#                                                                                  'out_refund', 'in_refund'))
#             res['price_subtotal'] = taxes_res['total_excluded']
#             res['price_total'] = taxes_res['total_included'] - amount_discount
#
#         else:
#             res['price_subtotal'] = subtotal
#             res['price_total'] = subtotal - amount_discount
#         res['amount_discount'] = amount_discount
#         # In case of multi currency, round before it's use for computing debit credit
#         if currency:
#             res = {k: currency.round(v) for k, v in res.items()}
#         return res
#
#     def _recompute_tax_lines(self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None):
#         """ Compute the dynamic tax lines of the journal entry.
#
#         :param recompute_tax_base_amount: Flag forcing only the recomputation of the `tax_base_amount` field.
#         """
#         self.ensure_one()
#         in_draft_mode = self != self._origin
#
#         def _serialize_tax_grouping_key(grouping_dict):
#             ''' Serialize the dictionary values to be used in the taxes_map.
#             :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
#             :return: A string representing the values.
#             '''
#             return '-'.join(str(v) for v in grouping_dict.values())
#
#         def _compute_base_line_taxes(base_line):
#             ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
#             amount_currency & balance could not be the same as the expected currency rate.
#             The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
#             :param base_line:   The account.move.line owning the taxes.
#             :return:            The result of the compute_all method.
#             '''
#             move = base_line.move_id
#
#             if move.is_invoice(include_receipts=True):
#                 handle_price_include = True
#                 sign = -1 if move.is_inbound() else 1
#                 quantity = base_line.quantity
#                 is_refund = move.move_type in ('out_refund', 'in_refund')
#                 price_unit_wo_discount = sign * base_line.price_unit
#             else:
#                 handle_price_include = False
#                 quantity = 1.0
#                 tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
#                 is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
#                 price_unit_wo_discount = base_line.amount_currency
#
#             return base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
#                 base_line.price_unit,
#                 currency=base_line.currency_id,
#                 quantity=quantity,
#                 product=base_line.product_id,
#                 partner=base_line.partner_id,
#                 is_refund=is_refund,
#                 handle_price_include=handle_price_include,
#                 include_caba_tags=move.always_tax_exigible,
#             )
#
#         taxes_map = {}
#
#         # ==== Add tax lines ====
#         to_remove = self.env['account.move.line']
#         for line in self.line_ids.filtered('tax_repartition_line_id'):
#             grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
#             grouping_key = _serialize_tax_grouping_key(grouping_dict)
#             if grouping_key in taxes_map:
#                 # A line with the same key does already exist, we only need one
#                 # to modify it; we have to drop this one.
#                 to_remove += line
#             else:
#                 taxes_map[grouping_key] = {
#                     'tax_line': line,
#                     'amount': 0.0,
#                     'tax_base_amount': 0.0,
#                     'grouping_dict': False,
#                 }
#         if not recompute_tax_base_amount:
#             self.line_ids -= to_remove
#
#         # ==== Mount base lines ====
#         for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
#             # Don't call compute_all if there is no tax.
#             if not line.tax_ids:
#                 if not recompute_tax_base_amount:
#                     line.tax_tag_ids = [(5, 0, 0)]
#                 continue
#
#             compute_all_vals = _compute_base_line_taxes(line)
#
#             # Assign tags on base line
#             if not recompute_tax_base_amount:
#                 line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]
#
#             for tax_vals in compute_all_vals['taxes']:
#                 grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
#                 grouping_key = _serialize_tax_grouping_key(grouping_dict)
#
#                 tax_repartition_line = self.env['account.tax.repartition.line'].browse(
#                     tax_vals['tax_repartition_line_id'])
#                 tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
#
#                 taxes_map_entry = taxes_map.setdefault(grouping_key, {
#                     'tax_line': None,
#                     'amount': 0.0,
#                     'tax_base_amount': 0.0,
#                     'grouping_dict': False,
#                 })
#                 taxes_map_entry['amount'] += tax_vals['amount']
#                 taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'],
#                                                                                        tax_repartition_line,
#                                                                                        tax_vals['group'])
#                 taxes_map_entry['grouping_dict'] = grouping_dict
#
#         # ==== Pre-process taxes_map ====
#         taxes_map = self._preprocess_taxes_map(taxes_map)
#
#         # ==== Process taxes_map ====
#         for taxes_map_entry in taxes_map.values():
#             # The tax line is no longer used in any base lines, drop it.
#             if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
#                 if not recompute_tax_base_amount:
#                     self.line_ids -= taxes_map_entry['tax_line']
#                 continue
#
#             currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])
#
#             # Don't create tax lines with zero balance.
#             if currency.is_zero(taxes_map_entry['amount']):
#                 if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
#                     self.line_ids -= taxes_map_entry['tax_line']
#                 continue
#
#             # tax_base_amount field is expressed using the company currency.
#             tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id,
#                                                 self.company_id, self.date or fields.Date.context_today(self))
#
#             # Recompute only the tax_base_amount.
#             if recompute_tax_base_amount:
#                 if taxes_map_entry['tax_line']:
#                     taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
#                 continue
#
#             balance = currency._convert(
#                 taxes_map_entry['amount'],
#                 self.company_currency_id,
#                 self.company_id,
#                 self.date or fields.Date.context_today(self),
#             )
#             amount_currency = currency.round(taxes_map_entry['amount'])
#             amount_discount = (quantity * price_unit * discount) / 100
#             sign = -1 if self.is_inbound() else 1
#             to_write_on_line = {
#                 'amount_currency': amount_currency,
#                 'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
#                 'debit': balance > 0.0 and balance or 0.0,
#                 'credit': balance < 0.0 and -balance or 0.0,
#                 'tax_base_amount': tax_base_amount,
#                 'price_total': sign * amount_currency - amount_discount,
#                 'price_subtotal': sign * amount_currency - amount_discount,
#                 'amount_discount': amount_discount,
#             }
#
#             if taxes_map_entry['tax_line']:
#                 # Update an existing tax line.
#                 if tax_rep_lines_to_recompute and taxes_map_entry[
#                     'tax_line'].tax_repartition_line_id not in tax_rep_lines_to_recompute:
#                     continue
#
#                 taxes_map_entry['tax_line'].update(to_write_on_line)
#             else:
#                 # Create a new tax line.
#                 create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
#                     'account.move.line'].create
#                 tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
#                 tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
#
#                 if tax_rep_lines_to_recompute and tax_repartition_line not in tax_rep_lines_to_recompute:
#                     continue
#
#                 tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
#                 taxes_map_entry['tax_line'] = create_method({
#                     **to_write_on_line,
#                     'name': tax.name,
#                     'move_id': self.id,
#                     'company_id': self.company_id.id,
#                     'company_currency_id': self.company_currency_id.id,
#                     'tax_base_amount': tax_base_amount,
#                     'exclude_from_invoice_tab': True,
#                     **taxes_map_entry['grouping_dict'],
#                 })
#
#             if in_draft_mode:
#                 taxes_map_entry['tax_line'].update(
#                     taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))
#
#     @api.model
#     def _get_fields_onchange_balance_model(self, quantity, discount, amount_currency, move_type, currency, taxes,
#                                            price_subtotal, force_computation=False):
#         ''' This method is used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
#         in some accounting fields such as 'balance'.
#
#         This method is a bit complex as we need to handle some special cases.
#         For example, setting a positive balance with a 100% discount.
#
#         :param quantity:        The current quantity.
#         :param discount:        The current discount.
#         :param amount_currency: The new balance in line's currency.
#         :param move_type:       The type of the move.
#         :param currency:        The currency.
#         :param taxes:           The applied taxes.
#         :param price_subtotal:  The price_subtotal.
#         :return:                A dictionary containing 'quantity', 'discount', 'price_unit'.
#         '''
#         if move_type in self.move_id.get_outbound_types():
#             sign = 1
#         elif move_type in self.move_id.get_inbound_types():
#             sign = -1
#         else:
#             sign = 1
#         amount_currency *= sign
#
#         # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
#         # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
#         # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
#         # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
#         # issue.
#         if not force_computation and currency.is_zero(amount_currency - price_subtotal):
#             return {}
#
#         taxes = taxes.flatten_taxes_hierarchy()
#         if taxes and any(tax.price_include for tax in taxes):
#             # Inverse taxes. E.g:
#             #
#             # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
#             # -----------------------------------------------------------------------------------
#             # 110           | 10% incl, 5%  |                   | 100               | 115
#             # 10            |               | 10% incl          | 10                | 10
#             # 5             |               | 5%                | 5                 | 5
#             #
#             # When setting the balance to -200, the expected result is:
#             #
#             # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
#             # -----------------------------------------------------------------------------------
#             # 220           | 10% incl, 5%  |                   | 200               | 230
#             # 20            |               | 10% incl          | 20                | 20
#             # 10            |               | 5%                | 10                | 10
#             force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
#             taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(amount_currency,
#                                                                                       currency=currency,
#                                                                                       handle_price_include=False)
#             for tax_res in taxes_res['taxes']:
#                 tax = self.env['account.tax'].browse(tax_res['id'])
#                 if tax.price_include:
#                     amount_currency += tax_res['amount']
#
#         discount_factor = 1
#         if amount_currency and discount_factor:
#             # discount != 100%
#             vals = {
#                 'quantity': quantity or 1.0,
#                 'price_unit': amount_currency / (quantity or 1.0),
#             }
#         elif amount_currency and not discount_factor:
#             # discount == 100%
#             vals = {
#                 'quantity': quantity or 1.0,
#                 'discount': 0.0,
#                 'price_unit': amount_currency / (quantity or 1.0),
#             }
#         elif not discount_factor:
#             # balance of line is 0, but discount  == 100% so we display the normal unit_price
#             vals = {}
#         else:
#             # balance is 0, so unit price is 0 as well
#             vals = {'price_unit': 0.0}
#         return vals
#
#
#     @api.model
#     def _get_fields_onchange_subtotal_model(self, price_subtotal, move_type, currency, company, date):
#         ''' This method is used to recompute the values of 'amount_currency', 'debit', 'credit' due to a change made
#         in some business fields (affecting the 'price_subtotal' field).
#
#         :param price_subtotal:  The untaxed amount.
#         :param move_type:       The type of the move.
#         :param currency:        The line's currency.
#         :param company:         The move's company.
#         :param date:            The move's date.
#         :return:                A dictionary containing 'debit', 'credit', 'amount_currency'.
#         '''
#         if move_type in self.move_id.get_outbound_types():
#             sign = 1
#         elif move_type in self.move_id.get_inbound_types():
#             sign = -1
#         else:
#             sign = 1
#
#         amount_currency = price_subtotal * sign
#         balance = currency._convert(amount_currency, company.currency_id, company, date or fields.Date.context_today(self))
#         return {
#             'amount_currency': amount_currency,
#             'currency_id': currency.id,
#             'debit': balance > 0.0 and balance or 0.0,
#             'credit': balance < 0.0 and -balance or 0.0,
#         }
