# web scrapper for getting information about Real Estate Funds negotiated in Bovespa 
# the wescrapper gets information from http://fundsexplores.com.br
#
# inspired in: https://medium.com/the-andela-way/introduction-to-web-scraping-using-selenium-7ec377a8cf72 (en) and 
#              https://medium.com/@henriquecoura_87435/web-scraping-com-python-selenium-e-javascript-faa108f95bbe (pt-BR)
#
# using the Chrome webdriver enables to load the entire page, not only the response for a get command
# chromewebriver is downloaded from google's webpage https://sites.google.com/a/chromium.org/chromedriver/downloads
# the following commands are used to move the dirver to the correct folder:
#   unzip chromedriver_linux64.zip
#   chmod +x chromedriver
#   sudo mv -f chromedriver /usr/local/share/chromedriver
#   sudo ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver
#   sudo ln -s /usr/local/share/chromedriver /usr/bin/chromedriver

import logging as log # for logging what the script is doing
from typing import Type, List # for typing
from selenium import webdriver #  launch/initialize a browser
from selenium.webdriver.common.by import By # search with specific parameters
from selenium.webdriver.support.ui import WebDriverWait # wait page laoding content
from selenium.webdriver.support import expected_conditions as EC # determine if the page has loaded all content
from selenium.webdriver.remote.webelement import WebElement # for typing
from selenium.common.exceptions import TimeoutException # handling timeout
from core.data_utils import RealStateFund

CHROMEDRIVER_EXECUTABLE_PATH: str = '/usr/local/share/chromedriver'
PAGE_LOADING_TIMEOUT: int = 20

log.basicConfig(level=log.INFO)
log.info('Starting webscraper script')
log.info(f'Using cromedriver from path { CHROMEDRIVER_EXECUTABLE_PATH }')

# creating the options for the browser
log.info('Creating options - incognito')
option = webdriver.ChromeOptions()
option.add_argument(" - incognito") # creating a new instance of Chrome in incognito mode
option.add_argument('headless')
# option.add_argument('window-size=1920x1080')

# creating the browser instance
log.info('Creating browser instance')
browser = webdriver.Chrome(executable_path=CHROMEDRIVER_EXECUTABLE_PATH, chrome_options=option)

# getting the website content
url = 'https://www.fundsexplorer.com.br/funds'
log.info(f'Browser is getting url { url }')

browser.get(url)

funds_data: List[Type[RealStateFund]] = []

try:
    wait_load: str = "//div[@id='fiis-list-container']"
    elements: str = "//div[@class='item']"
    log.info(f'Waiting while { wait_load } is loading (max timeout { PAGE_LOADING_TIMEOUT })')

    WebDriverWait(browser, PAGE_LOADING_TIMEOUT).until(EC.visibility_of_element_located((By.XPATH, wait_load)))

    log.info('Section successfully loaded')
    log.info(f'Getting items { elements }')

    found_elements: List[Type[WebElement]] = browser.find_elements_by_xpath(elements)
    found_elements: List[str] = [element.text for element in found_elements] # converting to list instead of WebElement object

    for element in found_elements:
        splitted_element: List[str] = element.split("\n")
        funds_data.append(RealStateFund(splitted_element[0], splitted_element[1], splitted_element[3]))

    print([x for x in funds_data])
except TimeoutException:
    log.error("Timed out waiting for page to load")
    log.info("Quitting browser instance...")
    browser.quit()