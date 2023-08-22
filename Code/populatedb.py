from webscraper import WebScraper
from getpass import getpass
from mysql.connector import connect, Error

w = WebScraper("https://boardgamegeek.com/boardgame/224517/brass-birmingham")
username_list = w.get_usernames()

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