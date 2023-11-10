import os
import apiCalls
import datetime
import ast
import mongo
import dotenv
try:
    dotenv.load_dotenv(dotenv_path="Constants.env")
except Exception:
    pass
#gets User in User object if password is correct
def getUser(user_id,password):
    if mongo.authorize(user_id,password):
        user1 = User(user_id,os.getenv("DEFAULT_PASSWORD"))
        return user1
    else:
        return None
class User:
    #signs_up user in mongo if password is not default otherwise
    #creates instance but not any changein db

    def __init__(self,user_id,password,email=None):
        if password == os.getenv("DEFAULT_PASSWORD"): #for getting the user in db
            u = mongo.getUserDict(user_id)
            if u:
                self.user_id = user_id
                self.password = password
                self.user_email = u["email"]
                self.data = u["data"]
            else:
                raise Exception("No such User")
        else:
            if email:#for creating the user
                self.user_id = user_id
                self.password = password
                self.user_email = email
                self.data = {}
                if not mongo.insertUser(self):
                    raise Exception("User already exists")
                mongo.insertUser(self)
                self.password=os.getenv("DEFAULT_PASSWORD")
            else:
                raise Exception("Email field empty for new user")

    def getUserInfo(self):
        user_data = mongo.getUserDict(self.user_id)
        return user_data
    def addData(self,text):
        user_dict = apiCalls.askChatGpt(f"""Provide a dictionary from '{text}',with stock_name as key,
                                        (invested_amount, Date) tuple as value (date in dd-mm-yy as string).
                                        Note: Today is {datetime.date.today()}.""")
        user_dict = user_dict[user_dict.find("{"):user_dict.rfind("}")+1]
        user_dict = ast.literal_eval(user_dict)
        print(user_dict)
        new_data={}
        for stock in user_dict:
            required_data = mongo.getData(self.user_id,stock)
            new_data[stock] = {
                "invested_amount": user_dict[stock][0],
                "current_price": required_data.get("current_price"),
                "last_change": required_data.get("last_change"),
                "long_term_change": required_data.get("long_term_change"),
                "monthly_change": required_data.get("monthly_change"),
                "last_invested_at": user_dict[stock][1]
            }
        self.data = self.__combine(self.data,new_data)
        print(self.data)
        mongo.insertUserData(self.user_id,self.data)

    def updateData(self):
        new_data={}
        if self.data is not dict:
            self.data = ast.literal_eval(str(self.data))
        for stock in self.data:
            required_data = mongo.getData(self.user_id,stock)
            new_data[stock] = {
                "invested_amount": self.data[stock].get("invested_amount"),
                "current_price": required_data.get("current_price"),
                "last_change": required_data.get("last_change"),
                "long_term_change": required_data.get("long_term_change"),
                "monthly_change": required_data.get("monthly_change"),
                "last_invested_at": self.data[stock].get("last_invested_at")
            }
        mongo.insertUserData(self.user_id,new_data)
        self.data = new_data

    def deleteUser(self,password):
        mongo.deleteUser(self.user_id,password)
    def deleteData(self,stock_name):
        mongo.deleteData(self.user_id,stock_name)
        self.data.pop(stock_name)
        print(f"Data deleted of user {self.user_id} -> {self.data}")

    def __combine(self,dict1,dict2):
        print(dict2)
        if isinstance(dict1,dict):
            dict3 = dict(dict1)
        else:
            dict1 = {}
            dict3 = {}
        for k,v in dict2.items():
            if dict1.get(k):
                if self.ynprompt(f"Are you sure you want to overwrite stock data for {k}"):
                    dict3[k]=dict2[k]
                else:
                    dict3[k] = dict1[k]
            else:
                dict3[k]=dict2[k]
        return dict3

    def ynprompt(self,String):
        return True




