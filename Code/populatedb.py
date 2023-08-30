from webscraper import WebScraper
from getpass import getpass
from mysql.connector import connect, Error

if __name__ == "__main__":
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