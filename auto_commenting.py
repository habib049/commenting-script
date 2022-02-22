import random
import re
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

USER_NAME = 'Nick'
COMMENT = '{Nie mogą|Mogą} się przyznać, że to były {niemieckie|polskie|francuskie|holenderskie} obozy, by w {przyszłości|przeszłości} Niemcy nie musiały płacić odszkodowań i całą winę zwalić na Polaków... TSUE to banda {oszustów|fałszerzy}'
SEARCH_WORD = 'zaczyna'
DRIVERS_PATH = '/Users/habiburrehman/PycharmProjects/CommentScript/chromedriver.exe'


class File:
    def __init__(self):
        self.file_name = 'links.txt'

    def read_file(self):
        data = open(self.file_name, 'r')
        links = data.read().replace('[', '').replace(']', '').split(',')
        links = [link.strip() for link in links]
        return links


class Spinner:
    def _extract_options(self, comment):
        options = re.findall(r'{(.+?)}', comment)

        index = 0
        for option in options:
            comment = comment.replace('{' + option + '}', 'spin-' + str(index))
            index += 1

        return comment, options

    def spin_comment(self):
        comment, options = self._extract_options(COMMENT)

        for index, value in enumerate(options):
            options = value.split('|')
            selected_option = self._get_spinned_option(options)
            comment = comment.replace('spin-' + str(index), selected_option)

        return comment

    def _get_spinned_option(self, options):
        limit = len(options)
        index = random.randint(0, limit - 1)
        return options[index]


class Scrape:
    def __init__(self):
        opts = webdriver.ChromeOptions()
        # opts.headless = True
        service = Service(DRIVERS_PATH)
        self.driver = webdriver.Chrome('chromedriver.exe', options=opts)

        self.comments_css = '.sc-EHOje.sc-bZQynM.q1w81m-0.eOAnrX'
        self.comments_css_other_pages = 'div.sc-7hqr3i-0.am69kv-0.q1w81m-0.LsrOO'
        self.next_page_css = 'div.sc-7hqr3i-0.am69kv-0.r7tdk8-6.bEhGrL'
        self.comments_section_css = 'button.sc-EHOje.sc-bZQynM.sc-gisBJw.chaYLp.sc-10fph3w-2.cSWNT'
        self.comments_button_css = 'button.sc-7hqr3i-0.am69kv-0.sc-1e1snaj-1.blqZbh'
        self.cookies_css = 'button.luna1cf.qzwz5vt'
        self.cookies_button_xpath = '/html/body/div[2]/div/div[2]/div[3]/div/button[2]'
        self.comment_input_css = 'textarea.sc-7hqr3i-0.am69kv-0.gce00-0.dvfmXE'
        self.nick_input_css = 'input.sc-7hqr3i-0.am69kv-0.igccxy-0.ddMgiu'

        self.cookies_accepted = False
        self.internet_exception = False

    def collect_comments(self):
        file = File()
        links = ['https://www.o2.pl/informacje/lincz-w-lodzi-wdarli-sie-do-hotelu-bo-uslyszeli-plotke-6722009898777440a']

        for index, link in enumerate(links):
            print('\nLoading link' + str(index + 1) + '... ', end='')
            try:
                self.driver.get(link)
            except WebDriverException:
                print('Internet connection is not stable! Closing the bot')
                break
            print(' => loaded')

            if not self.cookies_accepted:
                self._accept_cookies()

            page_index = 1
            while True:
                print('Exploring comments page-' + str(page_index) + ' of link-' + str(index + 1))

                if page_index > 1:
                    comments_elements = self.driver.find_elements(By.CSS_SELECTOR, self.comments_css_other_pages)
                else:
                    comments_elements = self.driver.find_elements(By.CSS_SELECTOR, self.comments_css)

                comments = [comment.text for comment in comments_elements]

                if len(comments) != 0:

                    if_exist = self._check_special_word(comments)
                    if if_exist:

                        wait = WebDriverWait(self.driver, 10)
                        next_page = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, self.next_page_css)))

                        if next_page:
                            try:
                                print("int  try")
                                webdriver.ActionChains(self.driver).move_to_element(next_page).click(next_page).perform()
                            except StaleElementReferenceException:
                                print("int  except")
                                next_page = self.search_button(page_index + 1)
                                webdriver.ActionChains(self.driver).move_to_element(next_page).click(next_page).perform()

                            page_index += 1
                            print('Waiting for the next page to load')

                            try:
                                wait = WebDriverWait(self.driver, 20)
                                should_display = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.sc-7hqr3i-0.gFcGdM')))
                            except TimeoutException:
                                self.internet_exception = True
                                break

                            time.sleep(2)  # wait for the next page to load

                        else:
                            print('There is only one page and we found you search word in comments')
                            break
                    else:
                        print('We haven\'t found any you search word on this page')
                        self._post_comment()
                        break
                else:
                    print('No comment found')
                    self._post_comment()
                    break

            if self.internet_exception:
                print('Internet connection is not stable! Closing the bot')
                break

            print('__________________________________________________________')

    def _check_special_word(self, comments):
        for comment in comments:
            if SEARCH_WORD in comment:
                return True
        return False

    def _post_comment(self):
        print('Posting a comment', end='')
        spinner = Spinner()

        wait = WebDriverWait(self.driver, 10)

        try:
            comment_section = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.comments_section_css)))
            webdriver.ActionChains(self.driver).move_to_element(comment_section).click(comment_section).perform()
        except TimeoutException:
            print('\ncomment section Internet connection is not stable! Closing the bot')
            return

        try:
            post_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.comments_button_css)))
        except TimeoutException:
            print('\nInternet connection is not stable! Closing the bot')
            return

        comment = self.driver.find_element(By.CSS_SELECTOR, self.comment_input_css)
        nick = self.driver.find_element(By.CSS_SELECTOR, self.nick_input_css)

        comment.send_keys(spinner.spin_comment())
        nick.send_keys(USER_NAME)

        post_button.click()
        time.sleep(2)
        print(' => Comment Posted Successfully')

    def _accept_cookies(self):
        self.cookies_accepted = True
        print('Waiting fot the Cookies', end='')
        try:
            try:
                wait = WebDriverWait(self.driver, 10)
                button = wait.until(EC.element_to_be_clickable((By.XPATH, self.cookies_button_xpath)))
                button.click()
                print(' => Cookies Accepted')
            except TimeoutException:
                print(' => No cookies found')
            time.sleep(3)  # to load the page again
        except NoSuchElementException:
            pass

    def search_button(self, text):
        buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button.sc-7hqr3i-0.am69kv-0.sc-1e1snaj-1.fFuRNh.r7tdk8-4.isiAgP')
        for button in buttons:
            if button.text == str(text):
                return button
        return None


if __name__ == '__main__':
    s = Scrape()
    s.collect_comments()
