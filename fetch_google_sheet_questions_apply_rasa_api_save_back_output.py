from datetime import date
from datetime import timedelta
import requests
import json
import pandas as pd
from google_sheet_handler import Google_sheet_handler
import logger_hander

class Rasa_Test:

    # initialize RASA API
    def __init__(self):
        self.url = 'http://localhost:5005/webhooks/rest/webhook'

    def fetch_data(self, google_sheet, yesterday):
        """
            This function will Fetch data of specific date from google sheet & return converted list.
            :param google_sheet: Original google_sheet, yesterday: date
            :return: data columns in list
        """
        list_of_records = google_sheet.get_all_records()
        Question_list = []
        Email_id_list = []
        Intent_list = []
        Answer_list = []
        for records in list_of_records:
            if records.get('Date') == yesterday:
                question = records.get('question')
                email_id = records.get('email_id')
                answer = records.get('answer')
                Question_list.append(question)
                Email_id_list.append(email_id)
                Answer_list.append(answer)
                Intent_list.append("")
        logger.info("Data fetched from existing sheet Successfully..!")
        return Question_list, Email_id_list, Intent_list, Answer_list

    def call_rasa_api(self,question_list):
        """
        This function will call Rasa api for getting answer of questions
        :param question_list: user question_list from google sheet
        :return: response from rasa
        """
        Response_list = []
        try:
            for ques in question_list:
                payload = {"sender": "mee", "message": str(ques)}
                r = requests.post(self.url, data=json.dumps(payload))
                response_return = r.json()
                Response_list.append(response_return[0].get("text"))
            logger.info(" Got Response_list from Rasa API ")
            return Response_list
        except Exception as e:
            excepName = type(e).__name__
            logger.error(" Rasa API Issue : " + excepName)
            return excepName

    def find_yesterday_date(self):
        """
            This function will find yesterday date
            :param null
            :return: yesterday date in specific format
        """
        today = date.today()
        yesterday = today - timedelta(days=1)
        yesterday = yesterday.strftime('%b %d, %Y')
        return yesterday

    def check_cell_name_valid_or_not(self, sheet, List_cell_name):
        """
            This function will find cell name is right or wrong
            :param sheet: google sheet instance, List_cell_name: list of cell name
            :return: True or False
        """
        return Google_sheet_handler.find_cell(self, sheet, List_cell_name)

    def extract_data_and_return_dataframe_in_list(self, sheet):
        """
            This function will find existing sheet data pass to RASA API function return new dataframe in list
            :param sheet: google sheet instance
            :return: True or False
        """
        yesterday = self.find_yesterday_date()
        List_of_cell_name = ['Date', 'question', 'email_id', 'answer', 'name']

        # check cell name is valid or not
        flag = self.check_cell_name_valid_or_not(sheet, List_of_cell_name)
        if flag:
            question_list, email_id, intent_list, answer_list = self.fetch_data(sheet, yesterday)
            if len(question_list) != 0:
                Response_list = self.call_rasa_api(question_list)

                # if response got from rasa
                if Response_list != "ConnectionError":
                    dict = {'Date': yesterday, 'Email': email_id, 'Questions': question_list,
                            'bot1_intent': intent_list,
                            'bot1_answer': answer_list, 'bot2_intent': intent_list, 'bot2_answer': Response_list}
                    Rasa_dataframe = pd.DataFrame(dict)
                    df_list_value = Rasa_dataframe.values.tolist()
                    return df_list_value
            else:
                logger.info("No interaction happened in yesterday.")

if __name__ == "__main__":

    # create instances
    rasa_obj = Rasa_Test()
    sheet_handler = Google_sheet_handler()
    logger = logger_hander.set_logger()

    # get google sheet
    sheet = sheet_handler.call_sheet("Chatbot_Daily_Report","Chatbot_Daily_Report")
    if sheet != 'WorksheetNotFound':
        df_list_value = rasa_obj.extract_data_and_return_dataframe_in_list(sheet)
        created_sheet = sheet_handler.call_sheet("Chatbot_Daily_Report", "BL_BOT_Compare")
        if created_sheet != 'WorksheetNotFound':
            output = sheet_handler.save_output_into_sheet(created_sheet, df_list_value)
            logger.info(" Sheet Updated Successfully...!!!") if (output == True) else logger.error(" Something went wrong while Updating sheet ")