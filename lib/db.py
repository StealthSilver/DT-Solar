from pymongo import MongoClient
import config
class Database:
    def __init__(self):
        try:
            self.client=MongoClient(config.DBCONNECTIONSTRING)
            # self.client = MongoClient("mongodb://localhost:27017/")
            self.db =self.client.armax_prod_digitaltwin
        except:
            print("Database Connection not Establisted")
        
    def saveConfig(self, subdomain, doc):
        dtconfigCollection = self.db[subdomain]
        return dtconfigCollection.update_one(
            {"plantid": doc["plantid"]}, {"$set": doc}, upsert=True
        )

    def getConfig(self, subdomain, plantid):
        dtconfigCollection = self.db[subdomain]
        json_config = dtconfigCollection.find_one({"plantid": plantid})
        return json_config