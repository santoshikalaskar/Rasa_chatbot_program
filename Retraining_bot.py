import sklearn
from sklearn import preprocessing, svm
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
import re, os, pickle
from os.path import isfile, join
import nltk
import numpy as np
from datetime import date
from datetime import timedelta
import pandas as pd
from google_sheet_handler import Google_sheet_handler
import logger_hander

class ReTrain_bot:

    # initialize
    def __init__(self):
        pass

    def fetch_data(self, google_sheet, yesterday):
        """
            This function will Fetch data of specific date from google sheet & return converted list.
            :param google_sheet: Original google_sheet, yesterday: date
            :return: data columns in list
        """
        list_of_records = google_sheet.get_all_records()

        Question_list = []
        Email_id_list = []
        Bot1_intent_list = []
        bot2_intent_list = []
        Actual_intent_must_be = []
        Bot1_Result_List = []
        Bot2_Result_List = []

        for records in list_of_records:
            if ( records.get('Date') == yesterday and records.get('Question_is_proper_or_not') == "Right" ):
                question = records.get('Question')
                email_id = records.get('Email')
                Bot1_intent = records.get('BOT1_Intent')
                Bot2_intent = records.get('BOT2_Intent')
                Actual_intent = records.get('Actual_intent_must_be')
                Bot1_Result = records.get('Bot1_Result')
                Bot2_Result = records.get('Bot2_Result')

                Question_list.append(question)
                Email_id_list.append(email_id)
                Bot1_intent_list.append(Bot1_intent)
                bot2_intent_list.append(Bot2_intent)
                Actual_intent_must_be.append(Actual_intent)
                Bot1_Result_List.append(Bot1_Result)
                Bot2_Result_List.append(Bot2_Result)

        logger.info("Data fetched from existing sheet Successfully..!")
        return Email_id_list, Question_list, Bot1_intent_list, bot2_intent_list, Actual_intent_must_be, Bot1_Result_List, Bot2_Result_List

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

    def load_csv(self):
        path = "CC+FP_Data1.csv"
        data = pd.read_csv(path)
        data.drop_duplicates(['Question'], inplace=True)
        data.drop_duplicates(inplace=True)
        print("data shape: ",data.shape)
        return data

    def pre_processing_input(self, data):
        """
        This function will clean the received original data.
        :param data: Original data
        :return: cleaned data
        """
        regex = '[^a-z,A-Z]'
        tokenizer = nltk.tokenize.TweetTokenizer()
        lemma_function = nltk.stem.wordnet.WordNetLemmatizer()
        document = []
        for text in data.Question:
            collection = []
            tokens = tokenizer.tokenize(text)
            for token in tokens:
                # Apply regular expression to remove unwanted data.
                collection.append(lemma_function.lemmatize(re.sub(regex, " ", token.lower())))
            document.append(" ".join(collection))
        return document

    def pre_processing_label(self, data):
        """
        This function will convert categorical data(i.e., intent) into label encoded form.
        :param data: Original data
        :return: intent in numerical form
        """
        le = preprocessing.LabelEncoder()
        le.fit(data.Intent)
        label = le.transform(data.Intent)
        return label, le

    def countVectorFeaturizer(self, cleaned_data, label):
        """
        :param label: output values
        :param X_train: train data features
        :param X_test: test data features
        :param cleaned_data: cleaned data features
        :return: text data in the form of numbers
        """

        X_train, X_test, y_train, y_test = train_test_split(np.array(cleaned_data),
                                                            np.array(label),
                                                            test_size=0.1,
                                                            train_size=0.9,
                                                            random_state=42)

        count_vect = CountVectorizer(ngram_range=(1, 1))
        count_vect.fit(cleaned_data)
        X_train_cv = count_vect.transform(X_train)
        X_test_cv = count_vect.transform(X_test)
        return X_train_cv, y_train, X_test_cv, y_test, count_vect

    def train_model(self, X_train_cv, y_train, X_test_cv, y_test):
        """
        This function will train_model & retun accuracy, f1_score.
        :param X_train_cv, y_train, X_test_cv, y_test: Training data
        :return: f1, accuracy
        """
        svm = sklearn.svm.LinearSVC(C=0.1)
        svm.fit(X_train_cv, y_train)
        pred = svm.predict(X_test_cv)
        f1 = sklearn.metrics.f1_score(pred, y_test, average='weighted')
        accuracy = int(round(svm.score(X_test_cv, y_test) * 100))
        return svm, f1, accuracy

    def save_model(self, le, count_vect, classifier):
        """
        This function will save trained model
        :param le, count_vect, classifier: save paramenters into pickle file
        """
        obj = {'le': le, 'count_vect': count_vect, 'model': classifier}
        pickle.dump(obj, open('model/' + "model" + ".pickle", 'wb'))
        print("Model saved")

    def load_model(self):
        """
        This function will load save model file & return it
        """
        mypath = 'model/'
        model_file = [f for f in os.listdir(mypath) if (isfile(join(mypath, f)) and ("model" in f))][0]
        return model_file

    def Answer_Prediction(self, data, model_file):
        """
        This function will Predict Answer Intent of test data
        :param data, model_file: Testing data & loaded model
        :return: intent : return predicted intent of each question
        """
        model = pickle.load(open("model/" + model_file, 'rb'))
        le = model['le']
        count_vect = model['count_vect']
        classifier = model['model']
        cleaned_data = self.pre_processing_input(data)
        X_train_cv = count_vect.transform(cleaned_data)
        pred = classifier.predict(X_train_cv)
        intent = le.inverse_transform(pred)
        return intent[0]

    def call_retrian_model_predict_intent(self,retrain, Question_list):
        """
        This function will take user input data & perform Prediction of intent
        :param retrain, Question_list: class object, user question list from google sheet
        :return: intent : return predicted intent list of question list
        """
        model_file = retrain.load_model()
        questions_list = Question_list
        intent_list = []
        for question in questions_list:
            df = pd.DataFrame([{'Question': question}])
            intent = retrain.Answer_Prediction(df, model_file)
            intent_list.append(intent)
        return intent_list


if __name__ == "__main__":

    # create instances
    retrain_obj = ReTrain_bot()
    sheet_handler = Google_sheet_handler()
    logger = logger_hander.set_logger()

    # get google sheet
    sheet = sheet_handler.call_sheet("Chatbot_Daily_Report","BL_BOT_Compare")


    if sheet != 'WorksheetNotFound':
        yesterday = retrain_obj.find_yesterday_date()
        # yesterday = "Sep 21, 2020"
        print(yesterday)
        List_of_cell_name = ['Date','Email','Question','BOT1_Intent','BOT2_Intent','Question_is_proper_or_not', 'Actual_intent_must_be', 'Bot1_Result', 'Bot2_Result']

        # check cell name is valid or not
        flag = retrain_obj.check_cell_name_valid_or_not(sheet,List_of_cell_name)
        if flag:
            Email_id_list, Question_list, Bot1_intent_list, bot2_intent_list, Actual_intent_must_be, Bot1_Result_List, Bot2_Result_List = retrain_obj.fetch_data(sheet,yesterday)
            if len(Question_list) == 0:
                logger.info("No interaction happened in yesterday.")
            else:
                Retain_bot1_intent_list = retrain_obj.call_retrian_model_predict_intent(retrain_obj, Question_list)

                dict = {'Date': yesterday, 'Email': Email_id_list, 'Questions': Question_list, 'bot1_intent': Bot1_intent_list,
                     'bot2_intent': bot2_intent_list, 'Retain_bot1_intent': Retain_bot1_intent_list,'Actual_intent_must_be': Actual_intent_must_be, 'Bot1_Result_List': Bot1_Result_List, 'Bot2_Result_List': Bot2_Result_List }
                dataframe = pd.DataFrame(dict)
                print(len(dataframe))
                df_list_value = dataframe.values.tolist()

                # get google sheet to store result
                created_sheet = sheet_handler.call_sheet("ReTrain_BOT_data_Dump", "Retrain_bot_result")
                if created_sheet != 'WorksheetNotFound':
                    output = sheet_handler.save_output_into_sheet(created_sheet, df_list_value)
                    if output == True:
                        logger.info(" Sheet Updated Successfully...!!!")
                    else:
                        logger.error(" Something went wrong while Updating sheet ")
