# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class hta_report_deliveryslip(models.Model):
#     _name = 'hta_report_deliveryslip.hta_report_deliveryslip'
#     _description = 'hta_report_deliveryslip.hta_report_deliveryslip'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
