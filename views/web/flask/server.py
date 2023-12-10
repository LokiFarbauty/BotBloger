# import os
#
# from flask import Flask
# from pyngrok import ngrok
#
# os.environ["FLASK_ENV"] = "development"
# app = Flask(__name__)
# port = 5000
#
# #Setting an auth token allows us to open multiple tunnels at the same time
# ngrok.set_auth_token("2Z5QrqKaXmNDxWLk9kUBhAqTp3H_7Zv2sTYn5yyy4uAFP1Lof")
#
# # Open a ngrok tunnel to the HTTP server
# public_url = ngrok.connect(port).public_url
# print(" * ngrok tunnel \"{}\" -> \"http://127.0.0.1:{}\"".format(public_url, port))
# # Update any base URLs to use the public ngrok URL
# app.config["BASE_URL"] = public_url
# # Define Flask routes
# @app.route("/")
# def index():
#     return "Hello from Colab!"
# app.run()