# -*- coding: utf-8 -*-
# from odoo import http


# class HtaAccountReport(http.Controller):
#     @http.route('/hta_account_report/hta_account_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hta_account_report/hta_account_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hta_account_report.listing', {
#             'root': '/hta_account_report/hta_account_report',
#             'objects': http.request.env['hta_account_report.hta_account_report'].search([]),
#         })

#     @http.route('/hta_account_report/hta_account_report/objects/<model("hta_account_report.hta_account_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hta_account_report.object', {
#             'object': obj
#         })
