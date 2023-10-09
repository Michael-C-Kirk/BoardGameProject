import configparser
from flask import Flask, render_template, g
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

@app.route('/')
def home():
    conn = mysql.connect()
    cur = conn.cursor()
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