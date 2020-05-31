from typing import Type, List
import logging as log
import os
import datetime
from core.constants import FUNDSEXPLORER_BASE_URL, FUNDSEXPLORER_CHART_URL, DATA_FOLDER
from core.scraping_utils import FundsExplorerScraper
from core.data_utils import RealStateFund, convert_to_csv

print("Program started")

logname: str = DATA_FOLDER + f'{ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") } - Data scraping Log'
logfile: str = os.path.abspath(os.curdir) + logname

# log.basicConfig(level=log.INFO)
log.basicConfig(filename=logfile,
                    filemode='w',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=log.INFO)

if __name__ == "__main__":
    scraper: Type[FundsExplorerScraper] = FundsExplorerScraper(FUNDSEXPLORER_BASE_URL)

    funds_data: List[Type[RealStateFund]] = scraper.get_funds_list("/funds", "//div[@id='fiis-list-container']", "//div[@class='item']")

    for fund in funds_data:
        log.info("---------------------------------------------")
        log.info(f'Scraping information about fund { fund.ticker }')
        print(f'Getting fund { fund.ticker }')
        scraper.get_funds_prices(fund, FUNDSEXPLORER_CHART_URL)
        scraper.get_main_indicators(fund, "//section[@id='main-indicators']//span[not(contains(@class, 'indicator-value-unit'))]")
        scraper.get_basic_info(fund, "//section[@id='basic-infos']//span[contains(@class, 'title') or contains(@class, 'description')]")
        scraper.get_description(fund, "//section[@id='description']")
        scraper.get_dividends(fund, path="//div[@id='dividends-chart-wrapper']//script", container="//div[@id='dividends-chart-wrapper']")
        scraper.get_dividend_yield(fund, path="//div[@id='yields-chart-wrapper']//script", container="//div[@id='yields-chart-wrapper']")
        scraper.get_equity_value(fund, path="//div[@id='patrimonial-value-chart-wrapper']//script", container="//div[@id='patrimonial-value-chart-wrapper']")
        scraper.get_vacancy(fund, path="//div[@id='vacancy-chart-wrapper']//script", container="//div[@id='vacancy-chart-wrapper']")
        scraper.get_assets(fund, path_data="//div[@id='fund-actives-chart']//script", path_assets="//div[@id='fund-actives-items-wrapper']//div[@class='item']", container="//div[@id='vacancy-chart-wrapper']")

    scraper.close()

    print("Writing csv file")
    csvname: str = DATA_FOLDER + f'{ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") } - Funds Data.csv'
    csvfile: str = os.path.abspath(os.curdir) + csvname

    convert_to_csv(funds_data, csvfile)

    print("Program ended")