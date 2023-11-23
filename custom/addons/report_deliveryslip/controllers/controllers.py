# -*- coding: utf-8 -*-
# from odoo import http


# class HtaReportDeliveryslip(http.Controller):
#     @http.route('/hta_report_deliveryslip/hta_report_deliveryslip', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hta_report_deliveryslip/hta_report_deliveryslip/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hta_report_deliveryslip.listing', {
#             'root': '/hta_report_deliveryslip/hta_report_deliveryslip',
#             'objects': http.request.env['hta_report_deliveryslip.hta_report_deliveryslip'].search([]),
#         })

#     @http.route('/hta_report_deliveryslip/hta_report_deliveryslip/objects/<model("hta_report_deliveryslip.hta_report_deliveryslip"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hta_report_deliveryslip.object', {
#             'object': obj
#         })
