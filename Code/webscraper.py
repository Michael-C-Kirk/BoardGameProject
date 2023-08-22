from selenium import webdriver
from selenium.webdriver.common.by import By

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
        self.num_pages = int(self.driver.find_element(By.CSS_SELECTOR, 'a[ng-click="selectPage(totalPages)"]').text)

    def __collect_urls(self):
        self.__get_num_pages()

        for page_id in range(self.num_pages):
            self.url_list.append(self.rating_url.format(id = page_id))

    def __collect_usernames(self) -> None:
        self.__collect_urls()

        for url in self.url_list:
            cur_url = url
            self.driver.implicitly_wait(2)
            self.driver.get(cur_url)
            username_elems = self.driver.find_elements(By.CLASS_NAME, "comment-header-user.ng-binding")

            for e in username_elems:
                self.usernames.append((e.text, ))

    def get_usernames(self) -> list[tuple]:
        self.__collect_usernames()
        return self.usernames