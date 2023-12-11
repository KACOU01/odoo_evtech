# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    approve_limit_1 = fields.Monetary()
    expense_account_id = fields.Many2one("account.account", string="Compte")
    # approve_limit_2 = fields.Monetary()
    #daily_limit_1 = fields.Monetary()
    #daily_limit_2 = fields.Monetary()