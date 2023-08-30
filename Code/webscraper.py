from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from concurrent import futures
import threading
import time 
import numpy as np

class WebScraper:
    def __init__(self, url: str) -> None:
        self.rating_url = url + "/ratings?rated=1&pageid={id}"
        self.usernames = []
        self.url_list = []
        self.driver = self.__driver_setup()
        self.num_pages = 0
        self.thread_count = 6

    def __del__(self):
        self.driver.quit()

    def __driver_setup(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')

        driver = webdriver.Chrome()
        return driver
    
    def __get_num_pages(self) -> None:
        self.driver.get(self.rating_url.format(id = 1))
        self.num_pages = int(self.driver.find_element(By.CSS_SELECTOR, 'a[ng-click="selectPage(totalPages)"]').text)

    def __collect_urls(self):
        self.__get_num_pages()

        for page_id in range(1, self.num_pages + 1):
            self.url_list.append(self.rating_url.format(id = page_id))
        
        self.driver.quit()

    def __scrape_usernames(self, urls, driver):
        #print("Working on url: {u}".format(u = url))
        data = threading.local()
        for url in urls:
            driver.get(url)
            try:
                data.username_elems = WebDriverWait(driver, 6).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "comment-header-user.ng-binding")))
                time.sleep(1)
                for e in data.username_elems:
                    self.usernames.append((e.text, ))
            except TimeoutException:
                print("Error: Selenium Timeout Exception for url -> {url}".format(url=url))
                continue
            except NoSuchElementException:
                print("Error: Selenium NoSuchElement Exception for url -> {url}".format(url=url))
                continue
            


    def __mt_scrape_usernames(self) -> None:
        self.__collect_urls()

        drivers = [self.__driver_setup() for _ in range(self.thread_count)]
        chunks = np.array_split(self.url_list, self.thread_count)

        start_time = time.time()
        with futures.ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            executor.map(self.__scrape_usernames, chunks, drivers)
        print("--- %s seconds ---" % (time.time() - start_time))  

    def get_usernames(self) -> list[tuple]:
        self.__mt_scrape_usernames()
        return self.usernames

    def print_usernames(self):
        print(self.usernames, len(self.usernames))