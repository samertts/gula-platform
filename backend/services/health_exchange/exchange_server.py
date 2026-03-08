from flask import Flask, jsonify, request

from health_record_engine.record_manager import add_test_result

app = Flask(__name__)


@app.route("/exchange/lab_result", methods=["POST"])
def receive_result():

    data = request.json

    nhid = data["nhid"]
    test = data["test"]
    value = data["value"]

    add_test_result(nhid, test, value)

    return jsonify({"status": "stored"})


if __name__ == "__main__":

    app.run(port=9000)
