import configparser
from flask import Flask, request, render_template, g
from db import DataBaseAppFunctionality
from flaskext.mysql import MySQL

config = configparser.ConfigParser()
config.read("..\BoardGameProjectAdditonalFiles\config.ini")
username, password, host = (config["credentials"]["username"], config["credentials"]["password"], config["credentials"]["host"])

app = Flask(__name__)
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = username
app.config['MYSQL_DATABASE_PASSWORD'] = password
app.config['MYSQL_DATABASE_DB'] = 'boardgame_info'
app.config['MYSQL_DATABASE_HOST'] = host
mysql.init_app(app)

@app.route('/', methods=["POST","GET"])
def home():
    if request.method == "GET":
        conn = mysql.connect()
        db = DataBaseAppFunctionality(conn)
        bg_list = db.get_all_bgs() 

        return render_template('index.html', bg_list = bg_list)

if __name__ == "__main__":

    app.run(debug=True)