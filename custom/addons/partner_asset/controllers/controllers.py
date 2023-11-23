# -*- coding: utf-8 -*-
# from odoo import http


# class PartnerAsset(http.Controller):
#     @http.route('/partner_asset/partner_asset', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/partner_asset/partner_asset/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('partner_asset.listing', {
#             'root': '/partner_asset/partner_asset',
#             'objects': http.request.env['partner_asset.partner_asset'].search([]),
#         })

#     @http.route('/partner_asset/partner_asset/objects/<model("partner_asset.partner_asset"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('partner_asset.object', {
#             'object': obj
#         })
