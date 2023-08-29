from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent import futures
import threading
import time 

class WebScraper:
    def __init__(self, url: str) -> None:
        self.rating_url = url + "/ratings?rated=1&pageid={id}"
        self.usernames = []
        self.url_list = []
        self.driver = webdriver.Chrome()
        self.num_pages = 0

    def __del__(self):
        self.driver.quit()

    def __get_num_pages(self) -> None:
        self.driver.get(self.rating_url.format(id = 1))
        self.num_pages = 20 #int(self.driver.find_element(By.CSS_SELECTOR, 'a[ng-click="selectPage(totalPages)"]').text)

    def __collect_urls(self):
        self.__get_num_pages()

        for page_id in range(1, self.num_pages + 1):
            self.url_list.append(self.rating_url.format(id = page_id))

    def __scrape_usernames(self, url):
        #print("Working on url: {u}".format(u = url))
        data = threading.local()
        data.driver = webdriver.Chrome()
        data.driver.get(url)
        data.username_elems = WebDriverWait(data.driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "comment-header-user.ng-binding")))

        for e in data.username_elems:
            self.usernames.append((e.text, ))


    def __mp_scrape_usernames(self) -> None:
        self.__collect_urls()

        start_time = time.time()
        with futures.ThreadPoolExecutor(5) as executor:
            executor.map(self.__scrape_usernames, self.url_list)
        print("--- %s seconds ---" % (time.time() - start_time))  

    def get_usernames(self) -> list[tuple]:
        self.__mp_scrape_usernames()
        print(self.usernames)

if __name__ == "__main__":
    w = WebScraper("https://boardgamegeek.com/boardgame/224517/brass-birmingham")
    w.get_usernames()