from datetime import date
from datetime import timedelta
import requests
import json
import logging
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
        Name_list = []
        Intent_list = []
        Answer_list = []
        for records in list_of_records:
            if records.get('Date') == yesterday:
                question = records.get('question')
                email_id = records.get('email_id')
                answer = records.get('answer')
                name = records.get('name')
                Question_list.append(question)
                Email_id_list.append(email_id)
                Name_list.append(name)
                Answer_list.append(answer)
                Intent_list.append("")
        logger.info("Data fetched from existing sheet Successfully..!")
        return Question_list, Email_id_list, Name_list, Intent_list, Answer_list

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
        return Google_sheet_handler.find_cell(self, sheet, List_cell_name)

if __name__ == "__main__":

    # create instances
    rasa_obj = Rasa_Test()
    sheet_handler = Google_sheet_handler()
    logger = logger_hander.set_logger()

    # get google sheet
    sheet = sheet_handler.call_sheet("Chatbot_Daily_Report","Chatbot_Daily_Report")
    if sheet != 'WorksheetNotFound':
        yesterday = rasa_obj.find_yesterday_date()
        List_of_cell_name = ['Date','question','email_id','answer','name']

        # check cell name is valid or not
        flag = rasa_obj.check_cell_name_valid_or_not(sheet,List_of_cell_name)
        if flag:
            question_list, email_id, Name, intent_list, answer_list = rasa_obj.fetch_data(sheet,yesterday)
            if len(question_list) == 0:
                logger.info("No interaction happened in yesterday.")
            else:
                Response_list = rasa_obj.call_rasa_api(question_list)

                # if response got from rasa
                if Response_list != "ConnectionError":
                    dict = {'Date': yesterday, 'Email': email_id, 'Questions': question_list, 'bot1_intent': intent_list,
                         'bot1_answer': answer_list, 'bot2_intent': intent_list, 'Rasa_output': Response_list}
                    Rasa_dataframe = pd.DataFrame(dict)
                    df_list_value = Rasa_dataframe.values.tolist()

                    # get google sheet to store result
                    created_sheet = sheet_handler.call_sheet("Chatbot_Daily_Report", "BL_BOT_Compare")
                    if created_sheet != 'WorksheetNotFound':
                        output = sheet_handler.save_output_into_sheet(created_sheet, df_list_value)
                        if output == True:
                            logger.info(" Sheet Updated Successfully...!!!")
                        else:
                            logger.error(" Something went wrong while Updating sheet ")
