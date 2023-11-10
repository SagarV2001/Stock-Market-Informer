import openai
import os
import requests
import dotenv
import smtplib
try:
    dotenv.load_dotenv(dotenv_path="Constants.env")
except Exception:
    pass
#All API_KEYS ARE WILL BE LOADED ONLY WHEN MAIN SCRIPT IS RUN, SINCE DOTENV IS CALLED THERE
def askChatGpt(input):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=input,
        temperature=0.2,
        max_tokens=500
    )
    return response["choices"][0]["text"]
def getNews(**kwargs):
    news_params={
        "qInTitle":kwargs["topic_name"],
        # "sources":kwargs["sources"],
        "apiKey":os.getenv("NEWS_API_KEY")
    }
    news = requests.get("https://newsapi.org/v2/everything",params=news_params).json()["articles"][0:10]
    return news
def getStockData(stock_name):
    stock_parameters = {
        "function": "TIME_SERIES_DAILY",
        "symbol": stock_name,
        "apikey": os.getenv("STOCK_API_KEY")
    }
    stock_res = requests.get(url="https://www.alphavantage.co/query", params=stock_parameters).json()
    return stock_res["Time Series (Daily)"]
