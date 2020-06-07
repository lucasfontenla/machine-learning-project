import os
import json
import pandas as pd
import datetime as dt

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
                proc_data[key].append(funds_df_raw[key][line])

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

                    proc_data["Data de Constituição do Fundo"] = fund_date
                    proc_data["Cotas Emitidas"] = total_quotas
                    proc_data["Tipo de Gestão"] = mgmt_type
                    proc_data["Público Alvo"] = target
                    proc_data["Mandato"] = mandate
                    proc_data["Segmento"] = segment
                    proc_data["Prazo de Duração"] = term
                    proc_data["Taxa de Administração"] = admin_tax
                    proc_data["Taxa de Performance"] = perf_tax
    
    funds_df = pd.DataFrame(proc_data, columns=new_columns)

    out_path = os.path.abspath(os.curdir) + '\\data-processing\\data\\funds.pkl'
    funds_df.to_pickle(out_path)