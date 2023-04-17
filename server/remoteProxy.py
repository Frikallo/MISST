from flask import Flask, request, Response
import flask
import requests
from waitress import serve
import os
app = Flask(__name__)
SITE_NAME = "http://127.0.0.1:5001/"

@app.route("/")
def home():
    try:
        req = requests.get(SITE_NAME)
        return Response(req.content, status=req.status_code)
    except Exception as e:
        return Response(str(e), status=500)

@app.route("/queue", methods=["POST"])
def queue():
    try:
        req = requests.post(SITE_NAME + "queue")
        return Response(req.content, status=req.status_code)
    except Exception as e:
        return Response(str(e), status=500)
    
@app.route("/demucs-upload", methods=["POST"])
def upload():
    file = flask.request.files["file"]
    file.save(file.filename)
    try:
        req = requests.post(SITE_NAME + "demucs-upload", files={"file": open(file.filename, "rb")})
        os.remove(file.filename)
        return Response(req.content, status=req.status_code)
    except Exception as e:
        return Response(str(e), status=500)
    
@app.route("/getcoverart/<path:filename>", methods=["GET"])
def getcoverart(filename):
    try:
        req = requests.get(SITE_NAME + "getcoverart/" + filename)
        return Response(req.content, status=req.status_code)
    except Exception as e:
        return Response(str(e), status=500)
    
@app.route("/postcoverart", methods=["POST"])
def postcoverart():
    file = flask.request.files["file"]
    file.save(file.filename)
    try:
        req = requests.post(SITE_NAME + "postcoverart", files={"file": open(file.filename, "rb")})
        os.remove(file.filename)
        return Response(req.content, status=req.status_code)
    except Exception as e:
        return Response(str(e), status=500)
    
@app.route("/download/<path:filename>", methods=["GET"])
def download(filename):
    try:
        req = requests.get(SITE_NAME + "download/" + filename)
        return Response(req.content, status=req.status_code)
    except Exception as e:
        return Response(str(e), status=500)

@app.route("/getaverage", methods=["GET"])
def getaverage():
    try:
        req = requests.get(SITE_NAME + "getaverage")
        return Response(req.content, status=req.status_code)
    except Exception as e:
        return Response(str(e), status=500)

if __name__ == "__main__":
    serve(app, host="66.175.221.76", port=5001, threads=1)