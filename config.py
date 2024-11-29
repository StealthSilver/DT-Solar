import os
from dotenv import load_dotenv

load_dotenv()
# host = "localhost"
# port = 27017
# database = "plant_config_test"
# DBCONNECTIONSTRING = f"mongodb://{host}:{port}/"
DBCONNECTIONSTRING = os.getenv("DBCONNECTIONSTRING")
# print(DBCONNECTIONSTRING)

# APPLICATION_NAME = "DIGITALTWIN"
# DBCONNECTIONSTRING = os.getenv("DBCONNECTIONSTRING")
# SECRET_KEY = os.getenv("SECRET_KEY")
# LOGGERURL = os.getenv("LOGGERURL")
PORT = int(os.getenv("PORT") or 8000)
# DECIMAL_POINT = int(os.getenv("DECIMAL_POINT") or 3)
# PYTHON_ENV = os.getenv("PYTHON_ENV") or "development"
# DBNAME = os.getenv("DBNAME") or "smartgrid_digitaltwin_prod"
