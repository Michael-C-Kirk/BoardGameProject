from mysql.connector import connect, Error
import configparser

config = configparser.ConfigParser()
config.read("..\BoardGameProjectAdditonalFiles\config.ini")
username, password = config['credentials']['username'], config['credentials']['password']

def create_table_db(query):
    try:
        with connect(host="localhost",user=username,password=password,database="boardgame_info",) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                connection.commit()
    except Error as e:
        print(e)


create_boardgames_table_query = """
    CREATE TABLE board_games(
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100)
        )
    """

create_ratings_table_query = """
    CREATE TABLE ratings(
        board_game_id INT,
        user_id INT,
        rating DECIMAL(3,1),
        FOREIGN KEY(board_game_id) REFERENCES board_games(id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        PRIMARY KEY(board_game_id, user_id)
        )
    """


if __name__ == "__main__":
    create_table_db(create_ratings_table_query)