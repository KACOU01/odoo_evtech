# -*- coding: utf-8 -*-

from odoo import models, fields, api


REQUEST_STATE = [
        ('draft', 'Brouillon'),
        ('submit', 'En attente'),
        ('validate', 'Valide'),
        ('to_approve', 'A approuver'),
        ('approve', 'Approuve'),
        ('authorize','Autorise'),
        ('to_cancel', 'Annule'),
        ('post', 'Paye'),
        ('reconcile', 'Lettre'),
        ('cancel', 'Rejete')
    ]

class ExpenseLine(models.Model):
    _name ='expense.line'
    _description = 'Custom expense line'
    
    
    @api.model
    def _default_employee_id(self):
        return self.env.user.employee_id
    
    @api.model
    def _get_analytic_domain(self):
        project_ids = self.env['project.project'].search([]).ids
        res = [('project_ids', 'not in', project_ids)]
        return res
    
    @api.model
    def _get_employee_id_domain(self):
        employee_ids = self.env['hr.employee'].search([]).ids
        res = [('address_home_id.property_account_payable_id', '!=', False), ('id', 'in', employee_ids)]
        return res
    
    
    name = fields.Char('Libellé', required=True)
    #request_state = fields.Selection(selection=REQUEST_STATE, string='Status', index=True, readonly=True, copy=False, default='draft', required=True, help='Expense Report State')
    employee_id = fields.Many2one('hr.employee', string="Employé", check_company=True,)
    user = fields.Many2one('res.users', string="Beneficiaire", required=True, related="expense_id.requested_by")
    expense_id = fields.Many2one('expense.request', string='Expense Request')
    date = fields.Datetime(readonly=True, related='expense_id.date', string="Date")
    amount = fields.Float("Montant", digits='Product Price')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    requested_by = fields.Many2one('res.users' ,'Demandeur', related='expense_id.requested_by')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.company.currency_id)
    account_id = fields.Many2one('account.account')
    department_id = fields.Many2one('hr.department')
    fleet_vehicle = fields.Many2one('fleet.vehicle')
    # delivery_zone = fields.Many2one('partner.delivery.zone')
    product_category = fields.Many2one('product.category')
    # analytic_tag_ids = fields.Many2many("account.analytic.tag", compute="_compute_analytic_tags")
    move_lines = fields.One2many("account.move.line", "expense_id")
    has_move_line = fields.Boolean(default=False)
    debit = fields.Float("Debit", digits='Product Price')
    credit = fields.Float("Credit", digits='Product Price')
    


    # @api.depends("product_category.analytic_tag", "delivery_zone.analytic_tag", "department_id.analytic_tag", "fleet_vehicle.analytic_tag")
    # def _compute_analytic_tags(self):
    #     for line  in self:
    #         analytic_tag = []
    #         product = line.product_category.analytic_tag or False
    #         zone = line.delivery_zone.analytic_tag or False
    #         department = line.department_id.analytic_tag or False
    #         vehicle = line.fleet_vehicle.analytic_tag or False
    #         if product:
    #             analytic_tag.append(product.id)
    #         if zone:
    #             analytic_tag.append(zone.id)
    #         if department:
    #             analytic_tag.append(department.id)
    #         if vehicle:
    #             analytic_tag.append(vehicle.id)
    #         line.analytic_tag_ids = analytic_tag

    def _get_account_move_line(self):
        pass

