from webscraper import WebScraper
from getpass import getpass
from mysql.connector import connect, Error, IntegrityError
from boardgamegeek import BGGClient, BGGApiRetryError

class DatabaseHelper:
    def __init__(self, connection) -> None:
        self.connection = connection

    def __get_users_plus_ids(self, num_rows = 100) -> list[tuple]:
        ids_and_usernames = []
        select_users_query = "SELECT * FROM users LIMIT {rows}".format(rows = num_rows)

        with self.connection.cursor() as cursor:
            cursor.execute(select_users_query)
            result = cursor.fetchall()
            for row in result:
                ids_and_usernames.append(row)
        
        return ids_and_usernames
    
    def __insert_bg(self, bg_name_list):
        query = """
        INSERT INTO board_games
        (name)
        VALUES(%s)
        """

        with self.connection.cursor() as cursor:
            cursor.executemany(query, bg_name_list)
            connection.commit()

    def __insert_rating(self, rating_info_list):
        query = """
        INSERT INTO ratings
        (board_game_id, user_id, rating)
        VALUES(%s, %s, %s)
        """

        with self.connection.cursor() as cursor:
            cursor.executemany(query, rating_info_list)
            connection.commit()
        
    def __get_bg_id(self, bg_name):
        bg_name = bg_name.replace("\"", "\\\"")
        query = """
        SELECT board_games.id 
        FROM boardgame_info.board_games 
        WHERE board_games.name = "{bg_name}";
        """.format(bg_name=bg_name)

        with self.connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()[0][0]

    def populate_bg_ratings_tables(self):
        ids_and_usernames = self.__get_users_plus_ids(40034)
        bgg = BGGClient()

        for user_id, username in ids_and_usernames:
            try:
                collection = bgg.collection(user_name=username, rated=True)
                for game in collection.items:
                    try:
                        self.__insert_bg([(game.name, )])
                    except IntegrityError:
                        """
                        Only have this error check when trying to add non unique bg to database
                        Not doing anything in this instance since we just want to ignore and continue on
                        """
                        pass
                    print(user_id, username, game.name, game.rating)

                    bg_id = self.__get_bg_id(game.name)
                    try:
                        self.__insert_rating([(bg_id, user_id, game.rating)])
                    except IntegrityError:
                        pass

            except BGGApiRetryError:
                print("ERROR: BGGApiRetryError meaning failed to retrieve users rated collection")
                continue



    

if __name__ == "__main__":
    '''
    w = WebScraper("https://boardgamegeek.com/boardgame/316554/dune-imperium")
    username_list = w.get_usernames()
    w.print_usernames()

    try:
        with connect(host = "localhost", user = input("Enter username: "), password = getpass("Enter password: "), database = "boardgame_info",) as connection:
            insert_users_query = """
            INSERT IGNORE INTO users
            (username)
            VALUES (%s)
            """

            with connection.cursor() as cursor:
                cursor.executemany(insert_users_query, username_list)
                connection.commit()

    except Error as e:
        print(e)
    '''
    with connect(host = "localhost", user = "root", password = "HC>tG[=6qo~s|yE", database = "boardgame_info",) as connection:

        d = DatabaseHelper(connection)
        d.populate_bg_ratings_tables()