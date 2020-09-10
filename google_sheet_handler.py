import gspread
from oauth2client.service_account import ServiceAccountCredentials
import gspread_dataframe as gd
import logging
import logger_hander

class Google_sheet_handler:

    def __init__(self):
        self.scope = ['https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', self.scope)
        self.client = gspread.authorize(self.creds)

    def call_sheet(self, sheet_name, worksheet_name):
        try:
            self.sheet = self.client.open(sheet_name).worksheet(worksheet_name)
            return self.sheet
        except Exception as e:
            excepName = type(e).__name__
            logger.error(excepName)
            return excepName

    def find_cell(self, sheet, List_cell_name):
        flag = True
        try:
            for cell_name in List_cell_name:
                cell = sheet.find(cell_name)
            return flag
        except gspread.exceptions.CellNotFound:
            flag = False
            logger.error("CellNotFound Exception")
            return flag


logger = logger_hander.set_logger()
