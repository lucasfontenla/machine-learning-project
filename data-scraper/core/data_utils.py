from typing import Dict, List, Type
import logging as log
import csv
import os

class RealStateFund:
    # class for handling a Real Estate Fund data
    def __init__(self, ticker: str, name: str, admin: str):
        # ticker is the Bovespa ticker of the fund XXXX11 or XXXX11B
        # name is the official name of the fund
        # admin is the legal person responsible for the fund
        self.ticker: str = ticker
        self.name: str = name
        self.admin: str = admin

        self.prices: Dict[str, str] = {}
        self.indicators: Dict[str, str] = {}
        self.description: str = ""
        self.basic_info: Dict[str, str] = {}
        self.dividends: List[List[str]] = []
        self.dividend_yield: List[List[str]] = []
        self.equity_value: List[List[str]] = []
        self.vacancy: Dict[str, List[str]] = {}
        self.assets: dict = {}
    
    def __str__(self):
        return f'{ self.ticker }: { self.name } ({ self.admin })'

    def add_prices(self, prices: Dict[str, str]):
        self.prices: Dict[str, str] = prices

    def add_main_indicators(self, indicators: Dict[str, str]):
        self.indicators: Dict[str, str] = indicators

    def add_description(self, description: str):
        self.description: str = description

    def add_basic_info(self, info: Dict[str, str]):
        self.basic_info: Dict[str, str] = info

    def add_dividends(self, dividends: List[List[str]]):
        self.dividends: List[List[str]] = dividends

    def add_dividend_yield(self, dividend_yield: List[List[str]]):
        self.dividend_yield: List[List[str]] = dividend_yield

    def add_equity_value(self, equity_value: List[List[str]]):
        self.equity_value: List[List[str]] = equity_value

    def add_vacancy(self, vacancy: Dict[str, List[str]]):
        self.vacancy: Dict[str, List[str]] = vacancy

    def add_assets(self, assets: dict):
        self.assets: dict = assets



def convert_to_csv(funds_data: List[Type[RealStateFund]], filename: str):
    log.info(f'Converting data from { len(funds_data) } funds')
    
    csv_columns: List[str] = ["Ticker", "Nome", "Administrador", "Cotações Históricas", "Principais Indicadores", "Descrição", "Informações Básicas", "Dividendos Históricos", 
        "Dividend Yield Histórico", "Valor Patrimonial Histórico", "Vacância Histórica", "Ativos Atuais"
    ]

    dict_data: List[Dict[str, str]] = []

    for fund in funds_data:
        try:
            log.info(f'Converting fund { fund.ticker } ...')
            dict_data.append(
                {
                    "Ticker": fund.ticker,
                    "Nome": fund.name,
                    "Administrador": fund.admin,
                    "Cotações Históricas": fund.prices,
                    "Principais Indicadores": fund.indicators,
                    "Descrição": fund.description,
                    "Informações Básicas": fund.basic_info,
                    "Dividendos Históricos": fund.dividends,
                    "Dividend Yield Histórico": fund.dividend_yield,
                    "Valor Patrimonial Histórico": fund.equity_value,
                    "Vacância Histórica": fund.vacancy,
                    "Ativos Atuais": fund.assets,
                }
            )

        except Exception as e:
            log.error(f'Failed to convert fund { fund.ticker } - { e }')

    log.info(f'Successfully converted { len(dict_data) } funds')
    log.info(f'Writting csv file { filename }')

    try:
        with open(filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for data in dict_data:
                writer.writerow(data)
                
    except IOError:
        log.error("I/O error")

    log.info(f'Successfully written csv file { filename }')