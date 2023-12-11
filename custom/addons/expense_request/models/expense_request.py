# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
import datetime


STATES = [
        ('draft', 'Brouillon'),
        ('submit', 'En attente'),
        ('validate', 'Valide'),
        ('post', 'Paye'),
        ('reconcile', 'Lettre'),
        ('cancel', 'Rejete')
    ]

READONLY_STATES = {
        'to_cancel': [('readonly', True)],
        }

class ExpenseRequest(models.Model):
    _name = 'expense.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Expense management"
    _order = "date desc, id desc"
    _check_company_auto = True
    
    
    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)
    
    def get_default_statement_id(self):
        date = datetime.date.today()
        month = date.month
        res = self.env['account.bank.statement'].search([('state', 'not in', ('posted', 'confirm')), ('journal_id.type', '=', 'cash')]).filtered(lambda l:l.date==date)
        if not res:
            raise UserError(
                    _(
                        "Veuillez contacter la comptabilite pour creer le journal caisse."
                    )
                )
        return res[0]
    
    name = fields.Char(default='/', copy=False)
    date = fields.Datetime(default=fields.Datetime.now, string="Date", readonly=True)
    approve_date = fields.Datetime()
    description = fields.Char('Objet de la dépense', required=True)
    amount_due = fields.Monetary(string="Montant avancé")
    amount_justify = fields.Monetary(string="Montant justifié", compute="_compute_amount_justify", store=True)
    amount_residual = fields.Monetary(string="Reste", compute="_compute_amount_residual", store=True)
    state = fields.Selection(selection=STATES, string='Status', index=True, readonly=True, tracking=True, copy=False, default='draft', help='Expense Report State')
    line_ids = fields.One2many('expense.line', 'expense_id', string='Expense Line',)
    move_lines = fields.One2many("expense.line", "expense_id", string="Journal items", domain=[("has_move_line", "=", True)])
    requested_by = fields.Many2one('res.users' ,'Démandeur', tracking=True, default=_get_default_requested_by)
    statement_id = fields.Many2one('account.bank.statement', string="Caisse", tracking=True)
    statement_line_ids = fields.One2many('account.bank.statement.line', 'expense_id')
    is_expense_approver = fields.Boolean(string="Is Approver", compute="_compute_is_expense_approver",)
    expense_approver = fields.Many2one('res.users', string="Valideur", states=READONLY_STATES)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Company', required=True, index=True, readonly=True, default=lambda self: self.env.company)
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type', 'in', ['cash', 'bank'])], states=READONLY_STATES, default=lambda self: self.env['account.journal'].search([('type', '=', 'cash')], limit=1))
    to_approve_allowed = fields.Boolean(compute="_compute_to_approve_allowed")
    account_id = fields.Many2one("account.account", related="company_id.expense_account_id", string="Compte")
    move_ids = fields.Many2many("account.move", compute="_get_move_count")
    move_count = fields.Float(compute="_get_move_count", default=0.0)
    #move_id = fields.Many2one("account.move")

    
    def _get_move_count(self):
        for rec in self:
            moves = self.env["account.move"].search([("expense_id", '=', rec.id)])
            rec.move_ids = moves
            rec.move_count = len(moves)
                    
    
    @api.depends('line_ids.amount')
    def _compute_amount_justify(self):
        for rec in self:
            rec.amount_justify = sum([line.amount for line in rec.line_ids])

    @api.depends('amount_justify', 'amount_due')
    def _compute_amount_residual(self):
        for rec in self:
            rec.amount_residual = rec.amount_due - rec.amount_justify
    
    def send_mail_to_approver(self, email_to):
        subject = 'NOTE DE FRAIS A VALIDER'
        recipients = email_to.email
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        message = "<p>Dear {0}</p>".format(email_to.name) + "<p>Vous avez une note de frais en attente de validation {0}</p>".format(self.name) + "<p>Cliquer sur le lien ci-dessous pour valider</p>"
        message_body = message + base_url
        template_obj = self.env['mail.mail']
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_to': email_to
        }
        template_id = template_obj.create(template_data)
        template_obj.send(template_id)
        template_id.send()
        return True
    
    @api.depends("state")
    def _compute_to_approve_allowed(self):
        for rec in self:
            rec.to_approve_allowed = rec.state == "validate"
    
    """This method will check approver limit"""
    @api.depends('amount_due', 'company_id.approve_limit_1',)
    def _compute_is_expense_approver(self):
        for req in self:
            limit_1 = req.company_id.approve_limit_1
            user = self.env.user
            approve = False
            if user.has_group('expense_request.group_expense_approver_1'):
                approve = True
            # elif user.has_group('expense_request.group_expense_approver_2'):
            #     if req.total_amount <= limit_2:
            #         approve = True
            # elif user.has_group('expense_request.group_expense_approver_1'):
            #     if req.total_amount <= limit_1:
            #         approve = True
            req.is_expense_approver = approve
            
            
    def action_submit(self):
        for line in self.line_ids:
            line.action_submit()
        self.state = "submit"
        return True
    
    def button_to_cancel(self):
        return self.write({'state': 'to_cancel'})#Annuler
    
    def button_authorize(self):
        if self.state not in  ['approve']:
            raise UserError(
                    _(
                        "Vous ne pouvez pas autoriser une dépense non approuvée!"
                    )
                )
        for line in self.line_ids:
            line.action_authorize()
        return self.write({'state': 'authorize'})
    
    def button_approve(self):
        return self.write({'state': 'validate'})
    
    def button_rejected(self):
        self.is_approver_check()
        if any(self.filtered(lambda expense: expense.state in ('post'))):
            raise UserError(_('You cannot reject expense which is approve or paid!'))
        self.mapped("line_ids").do_cancel()
        return self.write({"state": "draft"})
    
    def to_approve_allowed_check(self):
        for rec in self:
            if not rec.to_approve_allowed:
                raise UserError(
                    _(
                        "Vous ne pouvez pas faire cette action. Veuillez demander approbation pour"
                        ". (%s)"
                    )
                    % rec.name
                )
    def is_approver_check(self):
        for rec in self:
            if not rec.is_expense_approver:
                raise UserError(
                    _(
                        "Vous ne pouvez pas approuver cette demande. Problème de droit! "
                        ". (%s)"
                    )
                    % rec.name
                )
    
    def is_approve_check(self):
        for rec in self:
            if rec.balance_amount < rec.total_amount:
                raise UserError(
                    _(
                        "Solde en caisse insuffisant pour payer cette note de frais "
                        ". (%s)"
                    )
                    % rec.balance_amount
                )
    
    def action_post(self):
        self._create_account_move()
        self.write({"state": "post"})

    
    def action_validate(self):
        move_value = {
            'ref': self.name,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            }
        move_lines = []
        for line in self.line_ids.filtered(lambda l: not l.move_lines):
            debit_value = {
                "name": line.description,
                "account_id": line.account_id.id,
                "debit": line.debit,
                "credit": line.credit,
                "journal_id": self.journal_id.id,
                "analytic_tag_ids": line.analytic_tag_ids,
                "department_id": line.department_id,
                "fleet_vehicle": line.fleet_vehicle,
                "delivery_zone": line.delivery_zone,
                "product_category": line.product_category,
                "date": self.date,
                "expense_id": line.id,
            }
            credit_value = {
                "name": line.name,
                "account_id": self.journal_id.default_account_id.id,
                "debit": line.credit,
                "credit": line.debit,
                "journal_id": self.journal_id.id,
                "date": self.date,
                "expense_id": line.id,
            }
            debit = (0, 0, debit_value)
            credit = (0, 0, credit_value)
            move_lines.append(debit)
            move_lines.append(credit)
        move_value.update({'line_ids': move_lines})
        move = self.env["account.move"].create(move_value)
        move.write({"expense_id": self.id})
        self.write({"move_lines": move_lines})
        return move

    def action_reconcile_move_line(self):
        for rec in self:
            move = self._create_account_move()
            move.post()
    
    def create_account_move(self):
        statement = self._create_bank_statement()
        date = datetime.date.today()
        debit_account = self.account_id
        credit_account = self.journal_id.default_account_id
        ref = self.name
        company = self.company_id
        move_lines = []
        move_value = {
            'ref': self.name,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            }
        debit_value = {
            "name": self.description,
            "account_id": self.account_id.id,
            "debit": self.amount_due < 0.0 and -self.amount_due or 0.0,
            "credit": self.amount_due > 0.0 and self.amount_due or 0.0,
            "journal_id": self.journal_id.id,
            "date": self.date,
            }
        credit_value = {
            "name": self.name,
            "account_id": self.journal_id.default_account_id.id,
            "debit": self.amount_due > 0.0 and self.amount_due or 0.0,
            "credit": self.amount_due < 0.0 and -self.amount_due or 0.0,
            "journal_id": self.journal_id.id,
            "date": self.date,
            }
        debit = (0, 0, debit_value)
        credit = (0, 0, credit_value)
        move_lines.append(debit)
        move_lines.append(credit)
        move_value.update({'line_ids': move_lines})
        move = self.env['account.move'].create(move_value)
        move.write({"expense_id": self.id})
        for line in statement.line_ids:
            line.write({"is_reconciled": True, "move_id": move.id})
        statement.button_validate()
        move.post()
        return move
        
    """This create account_bank_statetment_line in bank_statement given in expense request"""
    def _create_bank_statement(self):
        #self.ensure_one()
        previous_statements = self.env["account.bank.statement"].search([('journal_id', "=", self.journal_id.id), ('date', '<=', self.date)], order='date desc, id desc')

        statement_value = {
            "balance_start": previous_statements[0].balance_end_real if previous_statements else 0,
            'journal_id': self.journal_id.id,
            "date": self.date,
            "company_id": self.company_id.id,
        }
        statement = self.env["account.bank.statement"].create(statement_value)
        statement_lines = {
            "date": self.date,
            "payment_ref": self.description + "-"  + self.name,
            "amount": self.amount_due if self.amount_due < 0 else -self.amount_due,
            "company_id": self.company_id.id,
            }
        value = []
        lines = (0, 0, statement_lines)
        value.append(lines)
        statement.write({'line_ids': value})
        statement.write({"balance_end_real": statement.balance_end})
        self.write({"statement_id": statement.id})
        statement.button_post()
        return statement

            
    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('expense.request.code') or '/'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('expense.request.code') or '/'
        request = super(ExpenseRequest, self).create(vals)
        return request
    
    def write(self, vals):
        res = super(ExpenseRequest, self).write(vals)
        return res