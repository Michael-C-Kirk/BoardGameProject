import configparser

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("..\BoardGameProjectAdditonalFiles\config.ini")
    username, password = (config["credentials"]["username"], config["credentials"]["password"])
