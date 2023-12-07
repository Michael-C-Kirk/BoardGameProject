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
    l = [] #list of all MySQL queried bgs
    if request.method == "POST": #POST called in index.html ajax function
        query = request.json
        bgs = db.auto_complete_search(query['bgInput'])
        for bg in bgs:
            l.append(bg[0]) #bgs structured like [('bg_name',) ... ]
        return jsonify({'bgs': l})
        
    return render_template('index.html', bg_list = l)

@app.route('/results', methods=["GET", "POST"]) 
def resultPage():
    jsdata = None
    if request.method == "POST":
        jsdata = request.json
        print(jsdata)
        res = db.gather_bg_stats(jsdata, 9)
        print(res)
        db.create_temp_table("temp_table", res)
        return jsonify({'html':render_template('results.html', d=res)})

@app.route('/test', methods=["GET", "POST"])
def test():
    if request.method == "GET":
        bg_info = db.get_temp_table_vals("temp_table")
        print(bg_info)
        return render_template('results.html', d=bg_info)
    

if __name__ == "__main__":
    app.run(debug=True)