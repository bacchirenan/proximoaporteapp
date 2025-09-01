import streamlit as st
import pandas as pd
import yfinance as yf

# ==============================
# Configuração inicial
# ==============================
st.set_page_config(page_title="Gestão de Carteira", layout="wide")
st.title("Gestão de Carteira")

# ==============================
# Funções auxiliares
# ==============================
def formatar_ticker(ticker: str) -> str:
    """Formata o ticker, adicionando .SA para ativos brasileiros"""
    if pd.isna(ticker):
        return None
    ticker = ticker.strip().upper()
    # Adicionar .SA para ações/FIIs brasileiras
    if (
        ticker.endswith("3") or ticker.endswith("4") or
        ticker.endswith("11") or ticker in ["BBDC3","BBDC4","ITUB4","PETR3","PETR4"]
    ):
        return ticker + ".SA"
    return ticker

def get_valor_atual(ticker: str):
    """Busca o preço atual do ativo no Yahoo Finance"""
    if pd.isna(ticker):
        return None
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period="5d")
        if not hist.empty:
            return hist["Close"].iloc[-1]
        else:
            last_price = ticker_obj.fast_info.get("last_price", None)
            if last_price is None:
                print(f"[DEBUG] Não achei preço para {ticker}")
            return last_price
    except Exception as e:
        print(f"[ERRO] {ticker}: {e}")
        return None

# ==============================
# Simulação: dados de planilha
# ==============================
data_carteira = {
    "Produto": [
        "AAPL - APPLE INC.",
        "BBDC3 - BRADESCO",
        "MXRF11 - FII MAXI REN",
        "ITUB4 - ITAUUNIBANCO",
        "MSFT - MICROSOFT CORPORATION"
    ],
    "ValorAplicado": [5000, 2000, 3000, 4000, 6000]
}

data_alocacao = {
    "Ativo": [
        "AAPL - APPLE INC.",
        "BBDC3 - BRADESCO",
        "MXRF11 - FII MAXI REN",
        "ITUB4 - ITAUUNIBANCO",
        "MSFT - MICROSOFT CORPORATION"
    ],
    "PercentualIdeal": [20, 15, 10, 25, 30]
}

df_carteira = pd.DataFrame(data_carteira)
df_alocacao = pd.DataFrame(data_alocacao)

# ==============================
# Limpeza dos tickers
# ==============================
df_carteira["Ticker"] = (
    df_carteira["Produto"]
    .str.split("-").str[0]
    .str.strip().str.upper()
    .apply(formatar_ticker)
)

df_alocacao["Ticker"] = (
    df_alocacao["Ativo"]
    .str.split("-").str[0]
    .str.strip().str.upper()
    .apply(formatar_ticker)
)

# ==============================
# Buscar preços atuais
# ==============================
df_carteira["ValorAtual"] = df_carteira["Ticker"].apply(get_valor_atual)

# ==============================
# Recomendações de Aporte (exemplo)
# ==============================
df_recomendacoes = df_alocacao.copy()
df_recomendacoes["ValorAtual"] = df_recomendacoes["Ticker"].apply(get_valor_atual)

# ==============================
# Exibir tabelas no Streamlit
# ==============================
st.subheader("Carteira Atual vs Alocação Ideal")
st.dataframe(df_carteira)

st.subheader("Recomendações de Aporte")
st.dataframe(df_recomendacoes)
