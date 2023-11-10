import time
import apiCalls
import mongo
import user
import pprint
import pymongo
import dotenv
dotenv.load_dotenv(dotenv_path="Constants.env")
# mongo.clearUserDB()
# mongo.clearStockDB()
# mongo.clearEmailDB()
pprint.pprint(mongo.getStockList())
pprint.pprint(mongo.getUserList())
pprint.pprint(mongo.getUserDetailList())


