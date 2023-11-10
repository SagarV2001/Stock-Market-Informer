import pymongo
import apiCalls
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["userdb"]
def clearUserDB():
    db.drop_collection("users")
def clearStockDB():
    db.drop_collection("stock_collection")
def clearEmailDB():
    db.drop_collection("email_collection")
def getUserDetailList():
    return [x for x in db["users"].find()]
def getUserList():
    return [x for x in db["email_collection"].find()]
def getStockList():
    return [x for x in db["stock_collection"].find()]
def deleteUser(user_id,password):
    if authorize(user_id,password):
        db["email_collection"].delete_one({"user_id":user_id})
        db["users"].delete_one({"user_id": user_id})
        print(f"User deleted -> {user_id}")
        return True
    return False
def insertUser(user):
    users = db["users"]
    emailCollection = db["email_collection"]
    if users.count_documents({"user_id":user.user_id}) > 0:
        return False
    else:
        users.insert_one({"user_id":user.user_id,"email":user.user_email,"password":user.password,"data":"{}"})
        emailCollection.insert_one({"email":user.user_email,"user_id":user.user_id})
        print(f"User Created -> {user.user_id}")
        return True
def getUserDict(user_id):
    return db["users"].find_one({"user_id":user_id})

def getUserName(email_or_username):
    ans = db["email_collection"].find_one({"email":email_or_username})
    return ans["user_id"] if ans else email_or_username
def getEmail(username):
    ans = db["email_collection"].find_one({"user_id":username})
    return ans["email"] if ans else None
def insertUserData(user_id,data):
    users = db["users"]
    users.find_one_and_update({"user_id":user_id},
                              {"$set":{"data":data}})
    print(users.find_one({"user_id":user_id}).get("data"))
    print(f"Data Inserted in -> {user_id}")

def deleteData(user_id,stock_name):
    users = db["users"]
    stock_collection = db["stock_collection"]
    users.update_one({"user_id":user_id}, {"$unset":{"data."+stock_name:""}})
    temp = stock_collection.find_one({"stock_name":stock_name})
    if temp:
        stock_collection.find_one_and_update({"stock_name":stock_name},{"$pull":{"user_list":getEmail(user_id)}})
    else:
        return
    if len(stock_collection.find_one({"stock_name":stock_name}).get("user_list")) == 0:
        stock_collection.delete_one({"stock_name":stock_name})
def getData(user_id,stock):
    stock_collection = db["stock_collection"]
    stock_data = stock_collection.find_one({"stock_name":stock})
    if stock_data:
        stock_collection.find_one_and_update({"stock_name":stock},{"$addToSet":{"user_list":getEmail(user_id)}})
        return stock_data
    else:
        stock_data_list = apiCalls.getStockData(stock)
        stock_data_list = [(k,v["4. close"]) for k,v in stock_data_list.items()]
        stock_data = {
            "stock_name":stock,
            "current_price":stock_data_list[0][1],
            "last_change":getLastChange(stock_data_list),
            "long_term_change":getLongTermChange(stock_data_list),
            "monthly_change":getMonthlyChange(stock_data_list),
            "user_list":[getEmail(user_id)]
        }
        stock_collection.insert_one(stock_data)
        return stock_data

def updateAndreturnUsersToNotify():
    try:
        members_to_alert = set()
        stock_collection = db["stock_collection"]
        stock_list = [x for x in stock_collection.find({})]
        print(stock_list)
        for x in stock_list:
            print(x)
            print(x["stock_name"])
            stock_data_list = apiCalls.getStockData(x["stock_name"])
            stock_data_list = [(k, v["4. close"]) for k, v in stock_data_list.items()]
            previous_price = float(x["current_price"])
            last_change = float(getLastChange(stock_data_list))
            long_term_change = float(getLongTermChange(stock_data_list))
            monthly_change = float(getMonthlyChange(stock_data_list))
            stock_collection.find_one_and_update({"stock_name":x["stock_name"]},{
                "$set":{
                    "current_price":stock_data_list[0][1],
                    "last_change":str(last_change),
                    "long_term_change":str(long_term_change),
                    "monthly_change":str(monthly_change),
                }
            })
            percent_change = (last_change/previous_price)*100
            if percent_change>=4:
                members_to_alert = members_to_alert | set(x["user_list"])
            print(stock_collection.find({"stock_name":x["stock_name"]}))
        return members_to_alert
    except Exception:
        raise Exception("Update Exception.")


def authorize(user_id,password):
    try:
        if db["users"].find_one({"user_id": user_id})["password"] == password:
            return True
    except:
        return False

def getLongTermChange(li):
    return round(float(li[0][1])-float(li[len(li)-1][1]),2)
def getMonthlyChange(li):
    return round(float(li[0][1]) - float(li[21][1]),2)
def getLastChange(li):
    return round(float(li[0][1]) - float(li[1][1]),2)