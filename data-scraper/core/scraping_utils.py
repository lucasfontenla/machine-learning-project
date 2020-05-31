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

import json
import logging as log
from typing import NewType, Type, List, Dict
from selenium import webdriver #  launch/initialize a browser
from selenium.webdriver.common.by import By # search with specific parameters
from selenium.webdriver.support.ui import WebDriverWait # wait page laoding content
from selenium.webdriver.support import expected_conditions as EC # determine if the page has loaded all content
from selenium.webdriver.remote.webelement import WebElement # for typing
from selenium.common.exceptions import TimeoutException # handling timeout

from core.constants import CHROMEDRIVER_EXECUTABLE_PATH, PAGE_LOADING_TIMEOUT, FUNDSEXPLORER_CHART_URL
from core.data_utils import RealStateFund

XPath = NewType('XPath', str)

class FundsExplorerScraper:
    def __init__(self, base_url: str):
        log.info('Starting webscraper script')
        self.base_url = base_url
        self.__create_browser_instance()


    def __create_browser_instance(self):
        log.info('Creating options for Chrome Browser')
        option = webdriver.ChromeOptions()
        option.add_argument(" - incognito") # creating a new instance of Chrome in incognito mode
        option.add_argument('headless')

        # creating the browser instance
        log.info(f'Creating browser instance using cromedriver from path { CHROMEDRIVER_EXECUTABLE_PATH }')
        self.browser = webdriver.Chrome(executable_path=CHROMEDRIVER_EXECUTABLE_PATH, chrome_options=option)
        

    def __get_page(self, url: str, base_url: str = ''):
        if base_url == '': 
            base_url = self.base_url

        full_url: str = base_url + url

        if not full_url == self.browser.current_url:
            log.info(f'Browser is getting { full_url }')
            self.browser.get(full_url)


    def __wait_browser_load(self, container: XPath):
        log.info(f'Waiting while browser is loading { container } (max timeout { PAGE_LOADING_TIMEOUT })')
        try:
            WebDriverWait(self.browser, PAGE_LOADING_TIMEOUT).until(EC.visibility_of_element_located((By.XPATH, container)))
            log.info('Container successfully loaded')
        except TimeoutException:
            log.error("Timed out waiting for page to load")
            raise TimeoutError


    def get_funds_list(self, url: str, container: XPath, items_location: XPath) -> List[Type[RealStateFund]]:
        self.__get_page(url=url)
        self.__wait_browser_load(container)

        log.info(f'Getting funds list from { items_location }')
        
        found_elements: List[Type[WebElement]] = self.browser.find_elements_by_xpath(items_location)
        found_elements: List[str] = [element.text for element in found_elements] # converting to list instead of WebElement object
        
        funds_list: List[Type[RealStateFund]] = []
        for index, element in enumerate(found_elements):
            if index > 1: break
            splitted_element: List[str] = element.split("\n")
            funds_list.append(RealStateFund(splitted_element[0], splitted_element[1], splitted_element[3]))
        
        number_of_funds: int = len(funds_list)
        if number_of_funds > 0:
            log.info(f'Got { number_of_funds } funds')
        else:
            log.warning(f'No funds were found')

        return funds_list


    def get_funds_prices(self, fund: Type[RealStateFund], url: str):
        container: str = "//body"
        try: 
            log.info(f'Getting prices of fund { fund.ticker }')

            price_url: str = url.replace("#", fund.ticker[0:4])
            self.__get_page("", price_url)
            self.__wait_browser_load(container)
            prices: Dict[str, str] = json.loads(self.browser.find_element_by_xpath(container).text)

            fund.add_prices(prices['stockReports'])
        
        except Exception as e:
            log.warning(f'Unable to get prices of { fund.ticker } - { e }')


    def get_main_indicators(self, fund: Type[RealStateFund], path: XPath):
        try: 
            log.info(f'Getting indicators of fund { fund.ticker }')

            url: str = f'/funds/{ fund.ticker.lower() }'
            self.__get_page(url=url)
            self.__wait_browser_load(path)
            
            elements: List[Type[WebElement]] = self.browser.find_elements_by_xpath(path)
            elements: List[str] = [element.text for element in elements]

            elements_dict: Dict[str, str] = {}
            for i in range(0, len(elements), 2):
                if elements[i] != "":
                    elements_dict[elements[i]] = elements[i+1]

            fund.add_main_indicators(elements_dict)
        
        except Exception as e:
            log.warning(f'Unable to get indicators of { fund.ticker } - { e }')
            fund.add_main_indicators({})


    def get_description(self, fund: Type[RealStateFund], path: XPath):
        try: 
            log.info(f'Getting description of fund { fund.ticker }')

            url: str = f'/funds/{ fund.ticker.lower() }'
            self.__get_page(url=url)
            self.__wait_browser_load(path)
            
            element: Type[WebElement] = self.browser.find_element_by_xpath(path)
            description: str = element.text

            fund.add_description(description)
        
        except Exception as e:
            log.warning(f'Unable to get description of { fund.ticker } - { e }')
            fund.add_description("")


    def get_basic_info(self, fund: Type[RealStateFund], path: XPath):
        try: 
            log.info(f'Getting basic info of fund { fund.ticker }')

            url: str = f'/funds/{ fund.ticker.lower() }'
            self.__get_page(url=url)
            self.__wait_browser_load(path)
            
            elements: List[Type[WebElement]] = self.browser.find_elements_by_xpath(path)
            elements: List[str] = [element.text for element in elements]

            elements_dict: Dict[str, str] = {}
            for i in range(0, len(elements), 2):
                if elements[i] != "":
                    elements_dict[elements[i]] = elements[i+1]

            fund.add_basic_info(elements_dict)
        
        except Exception as e:
            log.warning(f'Unable to get basic info of { fund.ticker } - { e }')
            fund.add_basic_info({})


    def get_dividends(self, fund: Type[RealStateFund], path: XPath, container: XPath):
        try: 
            log.info(f'Getting dividends of fund { fund.ticker }')

            url: str = f'/funds/{ fund.ticker.lower() }'
            self.__get_page(url=url)
            self.__wait_browser_load(container)
            
            element: str = self.browser.find_element_by_xpath(path).get_attribute("innerHTML")
            dividends: List[str] = element.split("[")
            dividends: List[List[str]] = json.loads("[[" + dividends[3].split("]")[0] + "], [" + dividends[6].split("]")[0] + "]]")

            fund.add_dividends(dividends)
        
        except Exception as e:
            log.warning(f'Unable to get dividends of fund { fund.ticker }')
            fund.add_dividends([[], []])


    def get_dividend_yield(self, fund: Type[RealStateFund], path: XPath, container: XPath):
        try: 
            log.info(f'Getting dividend yield of fund { fund.ticker }')

            url: str = f'/funds/{ fund.ticker.lower() }'
            self.__get_page(url=url)
            self.__wait_browser_load(container)
            
            element: str = self.browser.find_element_by_xpath(path).get_attribute("innerHTML")
            yields: List[str] = element.split("[")
            yields: List[List[str]] = json.loads("[[" + yields[3].split("]")[0] + "], [" + yields[6].split("]")[0] + "]]")

            fund.add_dividend_yield(yields)
        
        except Exception as e:
            log.warning(f'Unable to get dividend yield of fund { fund.ticker }')
            fund.add_dividend_yield([[], []])


    def get_equity_value(self, fund: Type[RealStateFund], path: XPath, container: XPath):
        try: 
            log.info(f'Getting equity value of fund { fund.ticker }')

            url: str = f'/funds/{ fund.ticker.lower() }'
            self.__get_page(url=url)
            self.__wait_browser_load(container)
            
            element: str = self.browser.find_element_by_xpath(path).get_attribute("innerHTML")
            equity: List[str] = element.split("[")
            equity: List[List[str]] = json.loads("[[" + equity[3].split("]")[0] + "], [" + equity[5].split("]")[0] + "]]")

            fund.add_equity_value(equity)
        
        except Exception as e:
            log.warning(f'Unable to get equity value of fund { fund.ticker }')
            fund.add_equity_value([[], []])


    def get_vacancy(self, fund: Type[RealStateFund], path: XPath, container: XPath):
        try: 
            log.info(f'Getting vacancy of fund { fund.ticker }')

            url: str = f'/funds/{ fund.ticker.lower() }'
            self.__get_page(url=url)
            self.__wait_browser_load(container)
            
            element: str = self.browser.find_element_by_xpath(path).get_attribute("innerHTML")
            vacancy: List[str] = element.split("[")
            vacancy: Dict[str, List[str]] = json.loads('{"date":[' + vacancy[3].split("]")[0] + '], "Ocupação Física":[' + vacancy[5].split("]")[0] + '], "Vacância Física":[' + vacancy[6].split("]")[0] + '], "Ocupação Financeira":[' + vacancy[7].split("]")[0] + '], "Vacância Financeira":[' + vacancy[8].split("]")[0] + "]}")

            fund.add_vacancy(vacancy)
        
        except Exception as e:
            log.warning(f'Unable to get vacancy of fund { fund.ticker }')
            fund.add_vacancy({})


    def get_assets(self, fund: Type[RealStateFund], path_data: XPath, path_assets: XPath, container: XPath):
        try: 
            log.info(f'Getting assets of fund { fund.ticker }')

            url: str = f'/funds/{ fund.ticker.lower() }'
            self.__get_page(url=url)
            self.__wait_browser_load(container)
            
            element: str = self.browser.find_element_by_xpath(path_data).get_attribute("innerHTML")
            assets_data: List[str] = element.split("[")
            assets_data: List[List[str]] = json.loads("[[" + assets_data[3].split("]")[0] + "], [" + assets_data[5].split("]")[0] + "]]")

            elements: List[Type[WebElement]] = self.browser.find_elements_by_xpath(path_assets)
            elements: List[str] = [element.text for element in elements]

            assets: Dict[str, Dict[str, str]] = {}
            for asset in elements:
                info_list: List[str] = asset.split("\n")
                asset_name: str = info_list.pop(0)
                
                assets[asset_name] = {}
                for info in info_list:
                    info_split: List[str] = info.split(":")
                    assets[asset_name][info_split[0]] = info_split[1]

            assets: dict = {"Assets": assets, "Location": assets_data}
            fund.add_assets(assets)
        
        except Exception as e:
            log.warning(f'Unable to get assets of fund { fund.ticker }')
            fund.add_assets({})


    def close(self):
        log.info("Quitting browser instance and closing scraper")
        self.browser.quit()
