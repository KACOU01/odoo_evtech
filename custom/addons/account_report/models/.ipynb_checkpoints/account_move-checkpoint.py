# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from num2words import num2words
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"
    
    @api.model
    def _default_note(self):
        return self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.env.company.invoice_terms or ''
    #num2words convert number to word
    def _num_to_words(self, num):
        def _num2words(number, lang):
            try:
                return num2words(number, lang=lang).title()
            except NotImplementedError:
                return num2words(number, lang='en').title()
        if num2words is None:
            logging.getLogger(__name__).warning("The library 'num2words' is missing, cannot render textual amounts.")
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
    
# class AccountMoveLine(models.Model):
#     _inherit = "account.move.line"
    
#     acompte = fields.Boolean(default=False)