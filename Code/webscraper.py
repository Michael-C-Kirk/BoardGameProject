from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from concurrent import futures
import threading
import time 
import numpy as np
import configparser
import xml.etree.ElementTree as ET
import re

config = configparser.ConfigParser()
config.read("..\BoardGameProjectAdditonalFiles\config.ini")
username, psw = (config["bgg_login"]["username"], config["bgg_login"]["password"])

class WebScraper:
    def __init__(self, url: str) -> None:
        self.rating_url = url + "/ratings?rated=1&pageid={id}"
        self.browse_url = url + "/page/{page_num}"
        self.usernames = []
        self.bgg_ids = []
        self.url_list = []
        self.driver = self.__driver_setup()
        self.num_pages = 0
        self.thread_count = 5
        self.bgg_login = [username, psw]

    def __del__(self):
        self.driver.quit()

    def __driver_setup(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=options)
        return driver
    
    def __get_num_pages(self) -> None:
        self.driver.get(self.browse_url.format(page_num = 1))
        self.num_pages = int(self.driver.find_element(By.CSS_SELECTOR, '[title*="last page"]').text[1:-1])
        self.driver.quit()
        """for ratings scrape"""
        #self.driver.get(self.rating_url.format(id = 1))
        #self.num_pages = int(self.driver.find_element(By.CSS_SELECTOR, 'a[ng-click="selectPage(totalPages)"]').text)

    def __collect_urls(self):
        self.__get_num_pages()
        for page_id in range(1, self.num_pages + 1):
            self.url_list.append(self.browse_url.format(page_num=page_id))

        """for getting page number for rating_url"""
        #for page_id in range(1, self.num_pages + 1):
        #    self.url_list.append(self.rating_url.format(id = page_id))
        
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

    def test(self):
        self.__mt_scrape_bgg_ids()
        return (self.bgg_ids)
    
    def _scrape_bgg_ids(self, urls, driver):
        """
        Input: List of urls to scrape, a web driver with all options take care of
        Output: List of unique bgg_id along with bg names
        """
        data = threading.local()
        for url in urls:
            print("Working on url: {u}".format(u = url))
            driver.get(url)
            maybe_signin_page = driver.current_url

            if maybe_signin_page != url:
                WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.ID, "inputUsername"))).send_keys(self.bgg_login[0])
                WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.ID, "inputPassword"))).send_keys(self.bgg_login[1])
                WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH, "//button[contains( text(), 'Sign In')]"))).click()
                WebDriverWait(driver, 6).until(lambda driver: driver.current_url != maybe_signin_page)
                time.sleep(120)

            try:
                data.username_elems = WebDriverWait(driver, 8).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "primary")))
                time.sleep(15)
                for e in data.username_elems:
                    bg_name, bgg_id = e.text, e.get_attribute('href').split('/')[-2]
                    self.bgg_ids.append((bgg_id, bg_name))

            except TimeoutException:
                print("Error: Selenium Timeout Exception for url -> {url}".format(url=url))
                continue
            except NoSuchElementException:
                print("Error: Selenium NoSuchElement Exception for url -> {url}".format(url=url))
                continue

    def __mt_scrape_bgg_ids(self) -> None:
        """
        Multithreaded function that calls upon _scrape_bgg_ids
        """
        self.__collect_urls()

        drivers = [self.__driver_setup() for _ in range(self.thread_count)]
        chunks = np.array_split(self.url_list, self.thread_count)

        start_time = time.time()
        with futures.ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            executor.map(self._scrape_bgg_ids, chunks, drivers)
        print("--- %s seconds ---" % (time.time() - start_time))  

    def extract_info_from_xml(self, url) -> dict:
        """
        Input: string for bgg_xml_api url
        Output: dict{description: str, 
                     image: str,
                     categories: lst,
                     mechanics: lst
                    }

        Useful for extracting additional info about board games from bgg_api
        """
        self.driver.get(url)
        root = ET.fromstring(self.driver.page_source)
        bg_cat, bg_mech = [], [] #categories and mechanics
        bg_info = {}

        for neighbor in root.iter('link'):
            if neighbor.attrib.get('type') == "boardgamecategory":
                bg_cat.append(neighbor.attrib.get('value'))
            elif neighbor.attrib.get('type') == "boardgamemechanic":
                bg_mech.append(neighbor.attrib.get('value'))

        for neighbor in root.iter('description'):
            bg_info["description"] = re.sub(r'[^a-zA-Z.\-,!? ]', '', neighbor.text)

        for neighbor in root.iter('image'):
            bg_info["image"] = neighbor.text

        bg_info["categories"], bg_info["mechanics"] = bg_cat, bg_mech
        
        return bg_info



if __name__ == "__main__":
    w = WebScraper("")
    print(w.extract_info_from_xml("https://boardgamegeek.com/xmlapi2/thing?id=342942"))