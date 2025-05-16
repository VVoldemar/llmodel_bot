from flask import Flask, Response, request, abort
import time
import dotenv

from pprint import pprint
from litellm import completion, stream_chunk_builder
import litellm
import os

from utils import *
from load_data import model_list, fallbacks

dotenv.load_dotenv(override=True)

litellm.force_ipv4 = True

app = Flask(__name__)



messages = [
       {"role": "user", "content": "Introduction to python"}
   ]



@app.route("/stream/<string:model>")
def stream2(model: str):
    return Response(generate(model), mimetype="text/plain")

@app.route("/stream/", methods=["POST"])
def stream():
    if not request.is_json:
        print(request.get_data())
        print(request.get_json())
        print(request.content_encoding)
        return abort(415, "Unsupported Media Type: Request must be JSON")
    
    data = request.get_json()
    print(data)
    if not data or not valid_model_request(data):
        return abort(400, "Bad Request: Invalid JSON data")
    
    if valid_model_request(data):
        model = data["model"]
        messages = data["messages"]

        return Response(generate(model, messages), mimetype="text/plain")

@app.route("/")
def strm():
    return "Work"

if __name__ == "__main__":
    app.run(port=5050)