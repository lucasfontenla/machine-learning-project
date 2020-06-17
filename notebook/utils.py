import pandas as pd
import numpy as np
import scipy as sp
import string
import datetime as dt
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder as SKLOneHotEncoder
from sklearn.feature_extraction.text import CountVectorizer as SKLCountVectorizer

class CategoryManager:
    def __init__(self):
        self.categories = {}
        
    def add_category(self, group_name, categories):
        self.categories[group_name] = categories

    def __str__(self):
        print(self.categories)

# drop rows
class DropRows(BaseEstimator, TransformerMixin):
    def __init__(self, rows=["Cotas Emitidas", "Tipo de Gestão",
                        "Público Alvo", "Mandato", "Segmento",
                        "Patrimônio Líquido", "Descrição"]):
        self.rows = rows

    def fit(self, x, y=None):
        return self
    
    def transform(self, X):
        return X.dropna(subset=self.rows).reset_index(drop=True)

# drop ticker row
class DropTickerAndName(BaseEstimator, TransformerMixin):
    def __init__(self, category_manager, cols=['Ticker', 'Nome']):
        self.cols = cols
        self.category_manager = category_manager

    def fit(self, x, y=None):
        return self

    def transform(self, X, y=None):
        self.category_manager.add_category(group_name="Ticker", categories=list(X["Ticker"]))
        self.category_manager.add_category(group_name="Nome", categories=list(X["Nome"]))
        return X.drop(columns=self.cols)

# drop columns
class DropColumns(BaseEstimator, TransformerMixin):
    def __init__(self, cols):
        self.cols = cols

    def fit(self, x, y=None):
        return self

    def transform(self, X):
        return X.drop(columns=self.cols)

class Convert2Float(BaseEstimator, TransformerMixin):
    def fit(self, x, y=None):
        return self

    def transform(self, X, y=None):
        columns = X.columns
        for column in columns:
            try:
                X[column] = X[column].astype(float)
            except ValueError:
                print(f"Unable to convert column '{ column }' to float")
            except TypeError:
                print(f"Unable to convert column '{ column }' to float")

        return X

# remove title
class CleanHeaders(BaseEstimator, TransformerMixin):
    def __init__(self, col):
        self.col_index = col
    
    def fit(self, x, y=None):
        return self
    
    def transform(self, X):
        all_rows = X.iloc[:,self.col_index]
        changed_column = [None]*len(all_rows)
        
        for row, series in enumerate(all_rows):  
            if not series == None and str(series) != 'nan':
                pos = series.find("DESCRIÇÃO")
                if pos == 0:
                    changed_column[row] = series[9:]
                else: 
                    changed_column[row] = series
                    
        X.iloc[:,self.col_index] = changed_column
        return X

# remove punctuation   
class CleanPunct(BaseEstimator, TransformerMixin):    
    def __init__(self, col):
        self.table_punct = str.maketrans({key: " " for key in string.punctuation.replace("$","").replace("%", "") + ' \t\n\r\f\v–'})
        self.col_index = col
        
    def fit(self, x, y=None):
        return self

    def transform(self, X):
        all_rows = X.iloc[:,self.col_index]
        changed_column = [None]*len(all_rows)
        
        for row, series in enumerate(all_rows):   
            X_clean = []             
            if not series == None and str(series) != 'nan':
                clean_doc = ' '.join(series.lower().translate(self.table_punct).split())
                X_clean.append(clean_doc)
                changed_column[row] = clean_doc
                
        X.iloc[:,self.col_index] = changed_column
        return X

# one hot encoding
class OneHotEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, col, category_manager):
        self.target_cols_names = col
        self.category_manager = category_manager

    def fit(self, x, y=None):
        return self

    def transform(self, X, y=None):
        for col in self.target_cols_names:
            encoder = SKLOneHotEncoder(categories='auto')

            X[col] = encoder.fit_transform(X[[col]])
            self.category_manager.add_category(group_name=col, categories=list(encoder.categories_[0]))

        return X

# one hot encoding
class CountVectorizer(BaseEstimator, TransformerMixin):
    def __init__(self, col):
        self.target_cols_names = col

    def fit(self, x, y=None):
        return self

    def transform(self, X, y=None):
        for col in self.target_cols_names:
            X[col] = SKLCountVectorizer().fit_transform(X[[col]])

        return X

# input foundation date based on first price
class InputDate(BaseEstimator, TransformerMixin):
    def __init__(self, col, ref_col):
        self.col_index = col
        self.ref_col_index = ref_col

    def fit(self, x, y=None):
        return self

    def transform(self, X, y=None):
        all_rows = X.iloc[:,self.col_index]
        all_ref_rows = X.iloc[:,self.ref_col_index]

        for row, series in enumerate(all_rows):
            if str(series) == 'NaT':
                ref_series = all_ref_rows[row]
                if ref_series == None:
                    X.iloc[row,self.col_index] = None
                else:
                    dates = sorted(ref_series[0])
                    X.iloc[row,self.col_index] = dates[0]
        
        return X

# fill column with desired method
class FillColumn(BaseEstimator, TransformerMixin):
    def __init__(self, col, method, const=None):
        self.col_index = col
        self.method = method
        self.const = const

    def fit(self, x, y=None):
        return self

    def transform(self, X, y=None):
        if self.method == 'mean':
            col_name = X.columns[self.col_index]
            X[col_name].fillna(X[col_name].mean(), inplace=True)

        elif self.method == 'const':
            col_name = X.columns[self.col_index]
            X[col_name].fillna(self.const, inplace=True)

        return X

# creates columns based on dividends
class ProcessDividends(BaseEstimator, TransformerMixin):
    # column index
    def __init__(self, col=17):
        self.col_index = col
        
    def fit(self, X, y=None):
        return self  # nothing else to do

    def transform(self, X, y=None):
        all_rows = X.iloc[:,self.col_index]
        
        new_columns = [[0]*len(all_rows) for _ in range(19)] # M1 -> M12 + ult. tri + mean + min + max + var + skew + kurt
        
        for row, series in enumerate(all_rows):                
            if not series == None:
                # ordenando por data
                dates, dividends = zip(*sorted(zip(series[0], series[1]), reverse=True))
                mean_dividends = np.mean(dividends)

                for index, date in enumerate(dates):              
                    month_n = ((dates[0]-date).days)//30

                    if month_n > 11: 
                        break
                        
                    else:
                        new_columns[month_n][row] = dividends[index]
                        
                                              
                new_columns[12][row] = sum([
                    float(new_columns[0][row] or 0), float(new_columns[1][row] or 0), float(new_columns[2][row] or 0)
                ])
                        
                indicators = sp.stats.describe(np.array(dividends))
                new_columns[13][row] = indicators.mean
                new_columns[14][row] = indicators.minmax[0]
                new_columns[15][row] = indicators.minmax[1]
                if mean_dividends == 0:
                    new_columns[16][row] = 0
                else:
                    new_columns[16][row] = np.sqrt(indicators.variance)/mean_dividends
                new_columns[17][row] = indicators.skewness
                new_columns[18][row] = indicators.kurtosis
              
        return_list = X
        for new_column in new_columns:
            return_list = np.c_[return_list, new_column]

        new_columns_names = list(X.columns)
        new_columns_names.extend([f'Div. M-{ index }' for index in range(12)])
        new_columns_names.extend(["Div. Acum. Últ. Trimestre", "Div. Média", "Div. Min", "Div. Max","Div. Desv. Pad. Rel.",
        "Div. Assimetria", "Div. Curtose"])

        return pd.DataFrame(np.c_[return_list], columns=new_columns_names) 

# creates columns based on prices
class ProcessPrices(BaseEstimator, TransformerMixin):
    # column index
    def __init__(self, col=16):
        self.col_index = col
    
    def _filter_date(self, d_to_compare, d, month_n):
        date_ref = d.replace(
            year=d.year if d.month > month_n else d.year - 1,
            month=d.month-month_n if d.month > month_n else 12-(month_n-1),
            day=1
        )
        
        return d_to_compare.month == date_ref.month and d_to_compare.year == date_ref.year
        
    def fit(self, X, y=None):
        return self  # nothing else to do

    def transform(self, X, y=None):
        all_rows = X.iloc[:,self.col_index]
        
        new_columns = [[0]*len(all_rows) for _ in range(19)] # (mean) M1 -> M12 + mean + 
                                                             #        min + max + var + skew + kurt + max_var_pct
        
        for row, series in enumerate(all_rows):
            if not series == None:
                # ordenando por data
                dates, prices = zip(*sorted(zip(series[0], series[1]), reverse=True))
                mean_price = np.mean(prices)

                for month_n in range(12):
                    indexes = [dates.index(date) for date in dates if self._filter_date(date, dates[0], month_n)]  
                    
                    if len(indexes) == 0:
                        month_prices = [0]
                    else:
                        month_prices = prices[min(indexes): max(indexes)+1]
                    
                    new_columns[month_n][row] = np.mean(month_prices)
                    
                indicators = sp.stats.describe(prices)
                new_columns[12][row] = indicators.mean
                new_columns[13][row] = indicators.minmax[0]
                new_columns[14][row] = indicators.minmax[1]
                if mean_price == 0:
                    new_columns[15][row] = 0
                else:
                    new_columns[15][row] = np.sqrt(indicators.variance)/mean_price
                new_columns[16][row] = indicators.skewness
                new_columns[17][row] = indicators.kurtosis
                if prices[-1] == 0:
                    new_columns[18][row] = 1
                else:
                    new_columns[18][row] = (prices[0]/prices[-1])
              
        return_list = X
        for new_column in new_columns:
            return_list = np.c_[return_list, new_column]
        
        new_columns_names = list(X.columns)
        new_columns_names.extend([f'Preços Média M-{ index }' for index in range(12)])
        new_columns_names.extend(["Preços Média", "Preços Min", "Preços Max","Preços Desv. Pad. Rel.", "Preços Assimetria",
        "Preços Curtose", "Preços Variação Total"])

        return pd.DataFrame(np.c_[return_list], columns=new_columns_names) 

# creates columns based on equity
class ProcessEquity(BaseEstimator, TransformerMixin):
    # column index
    def __init__(self, col=19):
        self.col_index = col
        
    def fit(self, X, y=None):
        return self  # nothing else to do

    def transform(self, X, y=None):
        all_rows = X.iloc[:,self.col_index]
        
        new_columns = [[0]*len(all_rows) for _ in range(19)] # M1 -> M12 + mean + min + max + var + skew + kurt
        
        for row, series in enumerate(all_rows):                
            if not series == None:
                # ordenando por data
                dates, equity = zip(*sorted(zip(series[0], series[1]), reverse=True))
                mean_equity = np.mean(equity)

                for index, date in enumerate(dates):              
                    month_n = ((dates[0]-date).days)//30

                    if month_n > 11: 
                        break
                        
                    else:
                        new_columns[month_n][row] = equity[index]
                        
                indicators = sp.stats.describe(np.array(equity))
                new_columns[12][row] = indicators.mean
                new_columns[13][row] = indicators.minmax[0]
                new_columns[14][row] = indicators.minmax[1]
                if mean_equity == 0:
                    new_columns[15][row] = 0
                else:
                    new_columns[15][row] = np.sqrt(indicators.variance)/mean_equity
                new_columns[16][row] = indicators.skewness
                new_columns[17][row] = indicators.kurtosis
                if equity[-1] == 0:
                    new_columns[18][row] = 1
                else:
                    new_columns[18][row] = (equity[0]/equity[-1])
              
        return_list = X
        for new_column in new_columns:
            return_list = np.c_[return_list, new_column]
        
        new_columns_names = list(X.columns)
        new_columns_names.extend([f'Val. Patr. M-{ index }' for index in range(12)])
        new_columns_names.extend(["Val. Patr. Média", "Val. Patr. Min", "Val. Patr. Max","Val. Patr. Desv. Pad. Rel.",
        "Val. Patr. Assimetria", "Val. Patr. Curtose", "Va. Patr. Variação Total"])

        return pd.DataFrame(np.c_[return_list], columns=new_columns_names) 

# creates columns based on vacancy
class ProcessVacancy(BaseEstimator, TransformerMixin):
    # column index
    def __init__(self, col=20):
        self.col_index = col
        
    def fit(self, X, y=None):
        return self  # nothing else to do

    def transform(self, X, y=None):
        all_rows = X.iloc[:,self.col_index]
        
        new_columns = [[0]*len(all_rows) for _ in range(18)] # M1 -> M12 + mean + min + max + var + skew + kurt
        
        for row, series in enumerate(all_rows):                
            if not series == None:
                # ordenando por data
                dates_unsorted = series['date']
                vacancy_unsorted = [vacancy/100 for vacancy in series['Vacância Física']]
                dates, vacancy = zip(*sorted(zip(dates_unsorted, vacancy_unsorted), reverse=True))
                mean_vacancy = np.mean(vacancy)

                for index, date in enumerate(dates):              
                    month_n = ((dates[0]-date).days)//30

                    if month_n > 11: 
                        break
                        
                    else:
                        new_columns[month_n][row] = vacancy[index]
                        
                indicators = sp.stats.describe(np.array(vacancy))
                new_columns[12][row] = indicators.mean
                new_columns[13][row] = indicators.minmax[0]
                new_columns[14][row] = indicators.minmax[1]
                if mean_vacancy == 0:
                    new_columns[15][row] = 0
                else:
                    new_columns[15][row] = np.sqrt(indicators.variance)/mean_vacancy
                new_columns[16][row] = indicators.skewness
                new_columns[17][row] = indicators.kurtosis
              
        return_list = X
        for new_column in new_columns:
            return_list = np.c_[return_list, new_column]
        
        new_columns_names = list(X.columns)
        new_columns_names.extend([f'Vacância M-{ index }' for index in range(12)])
        new_columns_names.extend(["Vacância Média", "Vacância Min", "Vacância Max","Vacância Desv. Pad. Rel.",
        "Vacância Assimetria", "Vacância Curtose"])

        return pd.DataFrame(np.c_[return_list], columns=new_columns_names)

# creates columns based on assets
class ProcessAssets(BaseEstimator, TransformerMixin):
    # column index
    def __init__(self, col=13):
        self.col_index = col
        
    def fit(self, X, y=None):
        return self  # nothing else to do

    def transform(self, X, y=None):
        all_rows = X.iloc[:,self.col_index]
        
        ufs = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 
               'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
        new_columns = [[np.zeros(len(ufs)) for __ in range(len(all_rows))] for _ in range(1)] # assets location

        for row, series in enumerate(all_rows):                
            if not series == None:
                assets_loc_uf = series['Location'][0]
                assets_area_uf = series['Location'][1]
                
                for uf_index, uf in enumerate(ufs):
                    if (uf in assets_loc_uf):
                        index = assets_loc_uf.index(uf)
                        new_columns[0][row][uf_index] = assets_area_uf[index]

        return_list = X
        for new_column in new_columns:
            return_list = np.c_[return_list, new_column]
        
        new_columns_names = list(X.columns)
        new_columns_names.extend([f"Área dos Ativos { uf }" for uf in ufs])

        return pd.DataFrame(np.c_[return_list], columns=new_columns_names)        