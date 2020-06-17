import os
import json
import pandas as pd
import datetime as dt
import math

months_dict = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12
}

if __name__ == "__main__":
    abs_path = os.path.abspath(os.curdir) + '\\data-processing\\data\\2020-05-31 23_04_05 - Funds Data.csv'
    funds_df_raw = pd.read_csv(abs_path, quotechar='"')
    
    proc_data = {
        "Ticker": [], "Nome": [], "Administrador": [], "Descrição": [], "Data de Constituição do Fundo": [], "Cotas Emitidas": [],
        "Tipo de Gestão": [],  "Público Alvo": [], "Mandato": [], "Segmento": [], "Prazo de Duração": [], "Taxa de Administração": [],
        "Taxa de Performance": [], "Ativos Atuais": [], "Liquidez Diária": [], "Patrimônio Líquido": [], "Cotações Históricas": [],
        "Dividendos Históricos": [], "Dividend Yield Histórico": [], "Valor Patrimonial Histórico": [], "Vacância Histórica": []
    }
    new_columns = proc_data.keys()

    for key in funds_df_raw.keys():

        for line in range(0,funds_df_raw.shape[0]):
            if key in new_columns:
                subset = funds_df_raw[key][line]
                if key in ["Ativos Atuais", "Cotações Históricas", "Dividendos Históricos",  "Dividend Yield Histórico", "Valor Patrimonial Histórico", "Vacância Histórica"]:
                    if subset in ["[]","[[], []]","{}"]:
                        subset = None

                    elif key in ["Dividendos Históricos", "Dividend Yield Histórico", "Valor Patrimonial Histórico"]:
                        parsed_obj = json.loads(subset.replace("\'", '\"'))
                        
                        dates = parsed_obj[0]
                        for index, date in enumerate(dates):
                            splitted = date.split("/")
                            parsed_date = dt.datetime(int(splitted[1]), months_dict[splitted[0].lower()], 1)
                            parsed_obj[0][index] = parsed_date

                        subset = parsed_obj
                    
                    elif key == "Cotações Históricas":
                        parsed_obj = json.loads(subset.replace("\'", '\"'))

                        data = [[], []]
                        for line in parsed_obj:
                            data[0].append(dt.datetime.strptime(line['data'], "%Y-%m-%d %H:%M:%S"))
                            data[1].append(float(line['fec']))

                        subset = data

                    elif key == "Vacância Histórica":
                        parsed_obj = json.loads(subset.replace("\'", '\"'))
                        dates = parsed_obj['date']

                        for index, date in enumerate(dates):
                            splitted = date.split("/")
                            parsed_date = dt.datetime(int(splitted[1]), months_dict[splitted[0].lower()], 1)
                            parsed_obj['date'][index] = parsed_date

                        subset = parsed_obj

                    else:
                        if "D'Ávila" in subset:
                            subset = subset.replace("D'Ávila", "D Ávila")
                        elif "D'ouro" in subset:
                            subset = subset.replace("D'ouro", "D ouro")
                        elif "d'Oeste" in subset:
                            subset = subset.replace("d'Oeste", "D Oeste")
                        elif "SAM'S" in subset:
                            subset = subset.replace("SAM'S",  "SAMS")
                        elif '"F"' in subset:
                            subset = subset.replace('"F"', "F")
                        subset = json.loads(subset.replace("\'", "\""))

                elif ("N/A" in str(subset) or "nan" in str(subset)) and not key == "Descrição":
                    subset = None
                proc_data[key].append(subset)

            else:
                subset = json.loads(funds_df_raw[key][line].replace("\'", "\""))
                if key == "Principais Indicadores":
                    liquidity = subset["Liquidez Diária"]
                    if "N/A" in liquidity:
                        liquidity = None
                    elif "." in liquidity:
                        liquidity = float(liquidity.replace(".", ""))
                    else:
                        liquidity = float(liquidity)

                    net_worth = subset["Patrimônio Líquido"]
                    if "," in net_worth:
                        net_worth = net_worth.replace(",", ".")
                    if "N/A" in net_worth:
                        net_worth = None
                    elif "bi" in net_worth:
                        net_worth = float(net_worth.split(" ")[1])*1e9
                    elif "mi" in net_worth:
                        net_worth = float(net_worth.split(" ")[1])*1e6
                    else:
                        net_worth = float(net_worth.split(" ")[1])*1e3

                    proc_data["Liquidez Diária"].append(liquidity)
                    proc_data["Patrimônio Líquido"].append(net_worth)

                elif key == "Informações Básicas":
                    fund_date = subset['DATA DA CONSTITUIÇÃO DO FUNDO']
                    total_quotas = subset['COTAS EMITIDAS']
                    mgmt_type = subset['TIPO DE GESTÃO']
                    target = subset['PÚBLICO-ALVO']
                    mandate = subset['MANDATO']
                    segment = subset['SEGMENTO']
                    term = subset['PRAZO DE DURAÇÃO']
                    admin_tax = subset['TAXA DE ADMINISTRAÇÃO']
                    perf_tax = subset['TAXA DE PERFORMANCE']

                    if "N/A" in fund_date:
                        fund_date = None
                    else:
                        fund_date = fund_date.split(" de ")
                        fund_date = dt.datetime(int(fund_date[2]), months_dict[fund_date[1].lower()], int(fund_date[0]))
                        
                    if "N/A" in total_quotas:
                        total_quotas = None
                    else:
                        total_quotas = float(total_quotas.replace(".", ""))

                    if "N/A" in mgmt_type:
                        mgmt_type = None
                    
                    if "N/A" in admin_tax:
                        admin_tax = None
                    
                    if "N/A" in perf_tax:
                        perf_tax = None

                    if "N/A" in target:
                        target = None

                    if "N/A" in segment:
                        segment = None

                    if "N/A" in mandate:
                        mandate = None

                    proc_data["Data de Constituição do Fundo"].append(fund_date)
                    proc_data["Cotas Emitidas"].append(total_quotas)
                    proc_data["Tipo de Gestão"].append(mgmt_type)
                    proc_data["Público Alvo"].append(target)
                    proc_data["Mandato"].append(mandate)
                    proc_data["Segmento"].append(segment)
                    proc_data["Prazo de Duração"].append(term)
                    proc_data["Taxa de Administração"].append(admin_tax)
                    proc_data["Taxa de Performance"].append(perf_tax)
    
    funds_df = pd.DataFrame(proc_data, columns=new_columns)

    out_path = os.path.abspath(os.curdir) + '\\data-processing\\data\\funds.pkl'
    funds_df.to_pickle(out_path)