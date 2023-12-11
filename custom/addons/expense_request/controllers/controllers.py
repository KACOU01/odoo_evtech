# -*- coding: utf-8 -*-
# from odoo import http


# class ExpenseRequest(http.Controller):
#     @http.route('/expense_request/expense_request', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/expense_request/expense_request/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('expense_request.listing', {
#             'root': '/expense_request/expense_request',
#             'objects': http.request.env['expense_request.expense_request'].search([]),
#         })

#     @http.route('/expense_request/expense_request/objects/<model("expense_request.expense_request"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('expense_request.object', {
#             'object': obj
#         })
