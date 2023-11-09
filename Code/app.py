import configparser
from flask import Flask, redirect, url_for, request, render_template, g, jsonify, session
from db import DataBaseAppFunctionality
from flaskext.mysql import MySQL
import json

config = configparser.ConfigParser()
config.read("..\BoardGameProjectAdditonalFiles\config.ini")
username, password, host = (config["credentials"]["username"], config["credentials"]["password"], config["credentials"]["host"])

app = Flask(__name__, template_folder="templates")
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = username
app.config['MYSQL_DATABASE_PASSWORD'] = password
app.config['MYSQL_DATABASE_DB'] = 'boardgame_info'
app.config['MYSQL_DATABASE_HOST'] = host
mysql.init_app(app)

app.config['SECRET_KEY'] = "placeholder_secret_key"

db = DataBaseAppFunctionality()

@app.route('/', methods=["POST","GET"])
def home():
    if request.method == "GET":
        #conn = mysql.connect()
        #db = DataBaseAppFunctionality(conn)
        bg_list = db.get_all_bgs() 
        return render_template('index.html', bg_list = bg_list)

@app.route('/results', methods=["GET", "POST"]) 
def resultPage():
    jsdata = None
    if request.method == "POST":
        jsdata = request.json
        print(jsdata)
        #conn = mysql.connect()
        #db = DataBaseAppFunctionality(conn)
        res = db.gather_bg_stats(jsdata, 9)
        #jsdata = res
        print(res)
        db.create_temp_table("temp_table", res)
        print("--------------------wow------------------------------")
        return jsonify({'html':render_template('results.html', d=res)})

@app.route('/test', methods=["GET", "POST"])
def test():
    if request.method == "GET":
        return render_template('results.html')
    

if __name__ == "__main__":

    app.run(debug=True)