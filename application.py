import sys
from flask import Flask, jsonify, make_response, request
from digital_twin_iterators import DigitalTwinProcess as dt
import traceback
import json
from lib.db import Database
import config

application = Flask(__name__)
db = Database()

@application.errorhandler(Exception)
def server_error(err):
    application.logger.exception(err)
    return (
        jsonify(
            {
                "error": True,
                "errorMessage": err.args,
                "stack": traceback.format_exc(),
            }
        ),
        500,
    )


@application.route("/")
def root():
    return jsonify({"message": "Welcome to DPP API Interface"})


@application.route("/dpp/data", methods=["POST"])
def dpp_receiver():
    # return "Hello world"
    try:
        inputdata = json.loads(request.data)
        timestamp = inputdata["timestamp"]
        plantid = inputdata["plantid"]
        subdomain = inputdata["subdomain"]

        plantdata=db.getConfig(subdomain, plantid)
        outputdata = dt({"plant": plantdata, "wmsdata": inputdata["data"]["wmsdata"], "timestamp": timestamp, 'rtdata': inputdata["data"]["rtdata"]})
        return jsonify(outputdata)
    except:
        raise Exception(sys.exc_info())

        
@application.route("/dpp/config", methods=["POST"])
def config_receiver():
    # return "Hello world"
    try:
        data_api_endpoint = json.loads(request.data)
        subdomain = data_api_endpoint["subdomain"]
        db.saveConfig(subdomain,data_api_endpoint)
        return 'Done'
    except:
        raise Exception(sys.exc_info())

@application.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify({"error": True, "errorMessage": "Not found!"}), 404)


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=config.PORT, debug=True)
