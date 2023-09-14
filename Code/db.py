from webscraper import WebScraper
from mysql.connector import connect, Error, IntegrityError
from boardgamegeek import BGGClient, BGGApiRetryError, BGGApiError, BGGItemNotFoundError
import configparser
from collections import defaultdict

class DatabaseHelper:
    def __init__(self, connection) -> None:
        self.connection = connection

    def _get_users_plus_ids(self) -> list[tuple]:
        """
        Returns a list of (user_id, username) from database
        query only looks for users that have no recorded bg ratings
        """
        ids_and_usernames = []
        select_users_query = """SELECT *
                                FROM boardgame_info.users
                                WHERE boardgame_info.users.id NOT IN (SELECT boardgame_info.ratings.user_id FROM boardgame_info.ratings);
                            """

        with self.connection.cursor() as cursor:
            cursor.execute(select_users_query)
            result = cursor.fetchall()
            for row in result:
                ids_and_usernames.append(row)
        
        return ids_and_usernames
    
    def _insert_bg(self, bg_name_list):
        query = """
        INSERT INTO board_games
        (name)
        VALUES(%s)
        """

        with self.connection.cursor() as cursor:
            cursor.executemany(query, bg_name_list)
            connection.commit()

    def _insert_rating(self, rating_info_list):
        query = """
        INSERT INTO ratings
        (board_game_id, user_id, rating)
        VALUES(%s, %s, %s)
        """

        with self.connection.cursor() as cursor:
            cursor.executemany(query, rating_info_list)
            connection.commit()
        
    def _get_bg_id(self, bg_name):
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
        ids_and_usernames = self._get_users_plus_ids()
        bgg = BGGClient()

        for user_id, username in ids_and_usernames:
            try:
                collection = bgg.collection(user_name=username, rated=True)
                for game in collection.items:
                    try:
                        self._insert_bg([(game.name, )])
                    except IntegrityError:
                        """
                        Only have this error check when trying to add non unique bg to database
                        Not doing anything in this instance since we just want to ignore and continue on
                        """
                        pass
                    print(user_id, username, game.name, game.rating)

                    bg_id = self._get_bg_id(game.name)
                    try:
                        self._insert_rating([(bg_id, user_id, game.rating)])
                    except IntegrityError:
                        pass

            except BGGApiRetryError:
                print("ERROR: BGGApiRetryError meaning failed to retrieve users rated collection for username: {u}".format(u = username))
                continue

            except BGGApiError:
                print("ERROR: BGGApiError meaning a connection could not be made to the api for username: {u}".format(u = username))
                continue

            except BGGItemNotFoundError:
                print("ERROR: BGGItemNotFoundError for username: {u}".format(u = username))

class DataBaseAppFunctionality:
    def __init__(self, connection) -> None:
        self.connection = connection

    def _get_bg_ids(self, bg_query_lst):
        bg_ids, bg_names_tuple = (), ()

        for bg_name in bg_query_lst:
            bg_name = bg_name.replace('"', '\\"')
            bg_names_tuple += (bg_name,)

        if len(bg_query_lst) == 1:
            bg_names_tuple = str(bg_names_tuple)[0:-2] + ")"

        query = """
            SELECT board_games.id 
            FROM boardgame_info.board_games 
            WHERE board_games.name IN {bg_query_lst};
            """.format(
            bg_query_lst=str(bg_names_tuple)
        )

        with self.connection.cursor() as cursor:
            cursor.execute(query)
            for bg_id in cursor.fetchall():
                bg_ids += (bg_id[0],)

        return bg_ids

    def _get_user_ids_have_rated(self, bg_ids):
        user_ids = ()

        if len(bg_ids) == 1:
            bg_ids = str(bg_ids)[0:-2] + ")"

        query = """
            SELECT C.user_id
            FROM (
                SELECT user_id, username, Count(user_id) AS RatingCount
                FROM boardgame_info.ratings
                INNER JOIN boardgame_info.users
                ON ratings.user_id = users.id
                WHERE board_game_id IN {bg_ids}
                GROUP BY user_id
            ) C
            WHERE C.RatingCount = {num_bgs};
        """.format(bg_ids=bg_ids, num_bgs=len(bg_ids) if type(bg_ids) == tuple else 1)

        with self.connection.cursor() as cursor:
            cursor.execute(query)
            for user_id in cursor.fetchall():
                user_ids += user_id

        return user_ids


    def _get_user_id_rated_above(self, bg_ids, user_id, rating):
        """
        This query is reponsible for returning a user id if the lowest rated boardgame is >= rating
        Returns list of one tuple which contains a single user_id
        """
        if len(bg_ids) == 1:
            bg_ids = str(bg_ids)[0:-2] + ")"

        query = """
                SELECT user_id
                FROM boardgame_info.ratings
                WHERE user_id = {id} AND ((SELECT MIN(rating)
                                        FROM boardgame_info.ratings
                                        WHERE user_id = {id} AND board_game_id IN {bg_ids}) >= {rating})
                LIMIT 1;
        """.format(id=user_id, bg_ids=bg_ids, rating=rating)

        with self.connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()


    def _get_all_bg_from_user(self, user_id, rating, bg_ids):
        if len(bg_ids) == 1:
            bg_ids = str(bg_ids)[0:-2] + ")"

        query = """
            SELECT name, rating
            FROM boardgame_info.ratings
            INNER JOIN boardgame_info.board_games
            ON ratings.board_game_id = board_games.id
            WHERE user_id = {user_id} AND rating >= {rating} AND board_game_id NOT IN {bg_ids};
        """.format(user_id=user_id, rating=rating, bg_ids=bg_ids)

        with self.connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()


    def gather_bg_stats(self, bg_query_lst, rating):
        bg_stats_dict = defaultdict(int)
        final_ids = ()
        bg_ids = self._get_bg_ids(bg_query_lst)
        user_ids = self._get_user_ids_have_rated(bg_ids)

        for id in user_ids:
            user_id = self._get_user_id_rated_above(bg_ids, id, rating)
            if user_id != None and user_id != []:
                final_ids += user_id[0]

        for id in final_ids:
            bg_stats = self._get_all_bg_from_user(id, rating, bg_ids)
            for bg_name, r in bg_stats:
                bg_stats_dict[bg_name] += 1

        print(sorted(bg_stats_dict.items(), key=lambda item: item[1]))


    

if __name__ == "__main__":
    """
    config is used to store/retrieve Database username and password
    helpful for keeping sensitive information away from github 
    """
    config = configparser.ConfigParser()
    config.read("..\BoardGameProjectAdditonalFiles\config.ini")
    username, password = config['credentials']['username'], config['credentials']['password']

    '''
    w = WebScraper("https://boardgamegeek.com/boardgame/167698/magic-gathering-arena-planeswalkers")
    username_list = w.get_usernames()
    w.print_usernames()

    try:
        with connect(host = "localhost", user = username, password = password, database = "boardgame_info",) as connection:
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

    '''
    with connect(host = "localhost", user = username, password = password, database = "boardgame_info",) as connection:

        d = DatabaseHelper(connection)
        d.populate_bg_ratings_tables()
    '''

    with connect(host = "localhost", user = username, password = password, database = "boardgame_info",) as connection:
        db_app = DataBaseAppFunctionality(connection)
        db_app.gather_bg_stats(["Smash Up", "Nemsis", "Mantis Falls"], 8)