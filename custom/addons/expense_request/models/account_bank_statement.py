# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'
    
    expense_ids = fields.One2many('expense.request', 'statement_id')
    
    
class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"
    
    debit = fields.Monetary(currency_field='currency_id')
    expense_id = fields.Many2one('expense.request',"Expense")
    credit_account = fields.Many2one('account.account', string='Credit Account')
    debit_account = fields.Many2one('account.account',string='Debit Account')
    