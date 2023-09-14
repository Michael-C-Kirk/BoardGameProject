from mysql.connector import connect, Error
import configparser
from collections import defaultdict


def get_bg_ids(bg_query_lst, connection):
    bg_ids, bg_names_tuple = (), ()

    for bg_name in bg_query_lst:
        bg_name = bg_name.replace('"', '\\"')
        bg_names_tuple += (bg_name,)

    query = """
        SELECT board_games.id 
        FROM boardgame_info.board_games 
        WHERE board_games.name IN {bg_query_lst};
        """.format(
        bg_query_lst=str(bg_names_tuple)
    )

    with connection.cursor() as cursor:
        cursor.execute(query)
        for bg_id in cursor.fetchall():
            bg_ids += (bg_id[0],)

    return bg_ids


def get_user_ids_have_rated(bg_ids, connection):
    user_ids = ()
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
    """.format(
        bg_ids=bg_ids, num_bgs=len(bg_ids)
    )

    with connection.cursor() as cursor:
        cursor.execute(query)
        for user_id in cursor.fetchall():
            user_ids += user_id

    return user_ids


def get_user_id_rated_above(bg_ids, user_id, rating, connection):
    """
    This query is reponsible for returning a user id if the lowest rated boardgame is >= rating
    Returns list of one tuple which contains a single user_id
    """
    query = """
            SELECT user_id
            FROM boardgame_info.ratings
            WHERE user_id = {id} AND ((SELECT MIN(rating)
                                    FROM boardgame_info.ratings
                                    WHERE user_id = {id} AND board_game_id IN {bg_ids}) >= {rating})
            LIMIT 1;
    """.format(
        id=user_id, bg_ids=bg_ids, rating=rating
    )

    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def get_all_bg_from_user(user_id, rating, bg_ids, connection):
    query = """
        SELECT name, rating
        FROM boardgame_info.ratings
        INNER JOIN boardgame_info.board_games
        ON ratings.board_game_id = board_games.id
        WHERE user_id = {user_id} AND rating >= {rating} AND board_game_id NOT IN {bg_ids};
    """.format(
        user_id=user_id, rating=rating, bg_ids=bg_ids
    )

    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def gather_bg_stats(bg_query_lst, rating, connection):
    bg_stats_dict = defaultdict(int)
    final_ids = ()
    bg_ids = get_bg_ids(bg_query_lst, connection)
    user_ids = get_user_ids_have_rated(bg_ids, connection)

    for id in user_ids:
        user_id = get_user_id_rated_above(bg_ids, id, rating, connection)
        if user_id != None and user_id != []:
            final_ids += user_id[0]

    for id in final_ids:
        bg_stats = get_all_bg_from_user(id, rating, bg_ids, connection)
        for bg_name, r in bg_stats:
            bg_stats_dict[bg_name] += 1

    print(sorted(bg_stats_dict.items(), key=lambda item: item[1]))


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("..\BoardGameProjectAdditonalFiles\config.ini")
    username, password = (config["credentials"]["username"], config["credentials"]["password"])

    with connect(host="localhost", user=username, password=password, database="boardgame_info") as connection:
        gather_bg_stats(["Nemsis", "Root", "Inis", "Bloodrage", "Kemet: Blood and Sand"], 9, connection)
