import configparser
from flask import Flask, render_template
from db import DataBaseAppFunctionality

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


config = configparser.ConfigParser()
config.read("..\BoardGameProjectAdditonalFiles\config.ini")
username, password = (config["credentials"]["username"], config["credentials"]["password"])

if __name__ == "__main__":
    app.run()