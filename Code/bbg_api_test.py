from boardgamegeek import BGGClient

if __name__ == "__main__":
    bgg = BGGClient()
    collection = bgg.collection(user_name="Juicy_Pear", rated=True)
    for game in collection.items:
        print(game.name, game.rating)