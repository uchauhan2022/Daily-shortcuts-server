from flask import Flask, request
import os
import helper
import threading
import logging
import json
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


logging.basicConfig(
    filename="record.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s",
)
app = Flask("server")
app.config.from_object("config.Config")

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/")
def home():
    return "Hello Utkarsh Chauhan"


@app.route("/getElectricityBill", methods=["GET"])
@limiter.limit("1 per minute")
def getElectricityBill():
    startDate = request.args.get("StartDate")
    endDate = request.args.get("EndDate")
    fetchBillThread = threading.Thread(
        target=helper.getElectricityBillThreaded,
        name="FetchBill",
        args=(
            startDate,
            endDate,
        ),
    )
    app.logger.info("starting getElectricityBillThreaded")
    fetchBillThread.start()
    return (
        json.dumps({"success": True, "status": "Bill requested"}),
        200,
        {"ContentType": "application/json"},
    )


@app.errorhandler(Exception)
def handle_error(error):
    return "Error"

# @app.route("/autoPull", methods=['POST'])
# def autoPull():
#     try:
#         os.system("sudo git pull")
#         return "SUCCESS",200
#     except:
#         return "FAIL",200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host=os.environ.get("APP_HOST"), port=port, debug=app.config["DEBUG"])
