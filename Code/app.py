import configparser
from flask import Flask, render_template, g
from db import DataBaseAppFunctionality
from flask_mysqldb import MySQL

config = configparser.ConfigParser()
config.read("..\BoardGameProjectAdditonalFiles\config.ini")
username, password, host = (config["credentials"]["username"], config["credentials"]["password"], config["credentials"]["host"])

app = Flask(__name__)

app.config['MYSQL_HOST'] = host
app.config['MYSQL_USER'] = username
app.config['MYSQL_PASSWORD'] = password
app.config['MYSQL_DB'] = 'boardgame_info'

mysql = MySQL(app)

@app.route('/')
def home():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT board_games.id 
        FROM boardgame_info.board_games 
        WHERE board_games.name = "Nemesis";
        """)
    rv = cur.fetchall()
    return str(rv)
    #return render_template('index.html')

if __name__ == "__main__":

    app.run(debug=True)