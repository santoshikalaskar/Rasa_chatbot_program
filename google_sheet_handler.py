import gspread
from oauth2client.service_account import ServiceAccountCredentials
import gspread_dataframe as gd
import logger_hander

class Google_sheet_handler:

    # initialize gspread details
    def __init__(self):
        self.scope = ['https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', self.scope)
        self.client = gspread.authorize(self.creds)

    def call_sheet(self, sheet_name, worksheet_name):
        """
            This function will open google sheet & return their instance
            :param sheet_name: google sheet name, worksheet_name: specific worksheet name
            :return: sheet instance
        """
        try:
            self.sheet = self.client.open(sheet_name).worksheet(worksheet_name)
            return self.sheet
        except Exception as e:
            excepName = type(e).__name__
            logger.error(excepName)
            return excepName

    def find_cell(self, sheet, List_cell_name):
        """
            This function will find columns name is correct or not
            :param sheet: google sheet instance, List_cell_name:list of google sheet cells name
            :return: true or flase
        """
        flag = True
        try:
            for cell_name in List_cell_name:
                cell = sheet.find(cell_name)
            return flag
        except gspread.exceptions.CellNotFound:
            flag = False
            logger.error("CellNotFound Exception")
            return flag

    def save_output_into_sheet(self, worksheet, df_list):
        """
            This function will Save & Append output into Google sheet
            :param worksheet: worksheet instance, df_list: list of data rows
            :return: true or worksheet not found exception
        """
        try:
            for row in df_list:
                worksheet.append_row(row)
            logger.info("Output response of Rasa has been appended Successfully..!")
            return True
        except Exception as e:
            excepName = type(e).__name__
            logger.error(" Updating google sheet " + excepName)
            return excepName

logger = logger_hander.set_logger()
