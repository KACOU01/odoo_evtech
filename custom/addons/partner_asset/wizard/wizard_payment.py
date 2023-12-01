from odoo import models, fields
import os
import base64
import pandas as pd
import io
# from six import StringIO
import xlrd
from odoo.exceptions import UserError
from xlrd import open_workbook


class ExcelImportWizard(models.TransientModel):
    _name = 'excel.import.wizard'
    _description = 'Wizard for Excel Import'

    # file = fields.Binary('Fichier Excel', required=True)
    file_name = fields.Char("File Name",default= '/odoo/Classeur1.xlsx')
    # path_absolute = fields.Char("Path Abosulte", compute="_compute_path", store=True)



    def create_or_get_usager(self, usager_name):
        usager = self.env['partner.usager'].search([('name', 'ilike', usager_name)],limit=1)
        if not usager:
            usager = self.env['partner.usager'].create({'name': usager_name})
        return usager

    def create_or_get_borne(self, borne_name):
        borne = self.env['partner.asset'].search([('name', 'ilike', borne_name)],limit=1)
        if not borne:
            borne = self.env['partner.asset'].create({'name': borne_name})
        return borne

    def create_or_get_payment(self, date_obj, usager, amount, borne_id):
        payment_record = self.env['partner.payment.usage'].search(
            [('asset_id', '=', borne_id.id), ('date', '=', str(date_obj)), ('usager_id', '=', usager.id),
             ('amount', '=', amount)])
        if not payment_record:
            payment_record = self.env['partner.payment.usage'].create({
                'date': str(date_obj),
                'usager_id': usager.id,
                'asset_id': borne_id.id,
                'amount': amount,

            })
        return payment_record

    def button_import_(self):
        # file_path = os.path.abspath(self.file_name)
        # print("Le chemin du fichier: ", file_path)
        if self.file_name:
            try:
                df = pd.read_excel(self.file_name)
                print(df)
                for index, row in df.iterrows():
                    date_str = row['DATE']
                    date_object = date_str.date()
                    # print(str(date_object), ' ', type(date_object))
                    usager_name = row['USAGER']
                    borne_name = row['BORNE']
                    montant = row['Montant']
                    # print(usager_name)
                    usager = self.create_or_get_usager(usager_name)
                    borne = self.create_or_get_borne(borne_name)
                    print(usager, ' ', borne)
                    payments = self.create_or_get_payment(date_object, usager[0], montant, borne[0])

            except FileNotFoundError:
                raise UserError('No such file or directory found. \n%s.' % self.file_name)
            except pd.errors.EmptyDataError:
                raise UserError('The Excel file is empty.')
            except pd.errors.ParserError:
                raise UserError('Error parsing the Excel file. Make sure it is a valid Excel file.')

        # if self.file_name:
        #     print("Nom du fichier", self.file_name)
        #     try:
        #         book = xlrd.open_workbook(filename=self.file_name)
        #     except FileNotFoundError:
        #         raise UserError('No such file or directory found. \n%s.' % self.file_name)
        #     except xlrd.biffh.XLRDError:
        #         raise UserError('Only excel files are supported.')
        #     for sheet in book.sheets():
        #         try:
        #             print(sheet.name)
        #             line_vals = []
        #             if sheet.name:
        #                 for row in range(sheet.nrows):
        #                     row_values = sheet.row_values(row)
        #                     print(row_values)
        #
        #         except IndexError:
        #             pass
            # df = pd.read_excel(io.BytesIO(self.file), engine='xlrd')
            # print(df)
            # for index, row in df.iterrows():
            #     date_str = row['DATE']
            #     date_object = date_str.date()
            #     print(str(date_object), ' ', type(date_object))
            #     usager_name = row['USAGER']
            #     borne_name = row['BORNE']
            #     montant = row['Montant']
            #     print(usager_name)
            #     usager = self.create_or_get_usager(usager_name)
            #     borne = self.create_or_get_borne(borne_name)
            #     print(usager, ' ', borne)
            #     payments = self.create_or_get_payment(date_object, usager[0], montant, borne[0])