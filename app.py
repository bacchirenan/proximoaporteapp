import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Gestão de Carteira", layout="wide")
st.title("Gestão de Carteira")

# URLs das planilhas CSV públicas
URL_CARTEIRA = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FylcFw3BDl5zTg6b9y6Hn5TxE4y9A8kLNg/export?format=csv&gid=0"
URL_ALOCACAO = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FylcFw3BDl5zTg6b9y6Hn5TxE4y9A8kLNg/export?format=csv&gid=123456789"

# ===== Importação das planilhas =====
df_carteira = pd.read_csv(URL_CARTEIRA, sep=",")
df_alocacao = pd.read_csv(URL_ALOCACAO, sep=",")

# Ajuste nomes para evitar falhas no merge
df_carteira["Produto"] = df_carteira["Produto"].str.strip().str.upper()
df_alocacao["Produto"] = df_alocacao["Produto"].str.strip().str.upper()

# Merge carteira + alocação
df = pd.merge(df_carteira, df_alocacao, on="Produto", how="left")

# Substituir valores N/A da alocação por 0%
df["ParticipacaoIdeal"] = df["ParticipacaoIdeal"].fillna(0)

# Cálculos
valor_total = df["SaldoBruto"].sum()
df["ParticipacaoAtual"] = df["SaldoBruto"] / valor_total * 100
df["Diferenca"] = df["ParticipacaoAtual"] - df["ParticipacaoIdeal"]

# Definir status
def definir_status(diff):
    if diff < -1:
        return "Comprar mais"
    elif diff > 1:
        return "Não comprar"
    else:
        return "Ok"

df["Status"] = df["Diferenca"].apply(definir_status)

# ===== Cotação atual (Yahoo Finance) =====
def get_preco(ticker):
    try:
        return yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1]
    except:
        return None

df["ValorAtual"] = df["TickerYF"].apply(get_preco)

# ===== Desconto (%) (para ativos com ValorAtual) =====
df["Desconto (%)"] = ((df["ValorAplicado"] / df["Quantidade"]) / df["ValorAtual"] - 1) * 100
df["Desconto (%)"] = df["Desconto (%)"].round(2)

# ===== Exibir tabelas separadas =====
df_exibir = df.rename(columns={
    "ValorAplicado": "Valor Aplicado",
    "SaldoBruto": "Saldo Bruto",
    "ParticipacaoAtual": "Participação Atual",
    "ParticipacaoIdeal": "Participação Ideal",
    "Diferenca": "Diferença"
})

# --- Ações nacionais ---
df_acoes = df_exibir[df_exibir["TickerYF"].str.endswith(".SA", na=False)]
df_acoes = df_acoes[~df_acoes["Produto"].str.endswith("11")]

st.subheader("Carteira Atual vs Alocação Ideal – Ações Nacionais")
st.dataframe(df_acoes[["Produto", "Valor Aplicado", "Saldo Bruto",
                       "Participação Atual", "Participação Ideal",
                       "Diferença", "Status", "ValorAtual", "Desconto (%)"]])

# --- Fundos imobiliários (FIIs) ---
df_fiis = df_exibir[df_exibir["Produto"].str.endswith("11")]

st.subheader("Carteira Atual vs Alocação Ideal – Fundos Imobiliários")
st.dataframe(df_fiis[["Produto", "Valor Aplicado", "Saldo Bruto",
                      "Participação Atual", "Participação Ideal",
                      "Diferença", "Status", "ValorAtual", "Desconto (%)"]])

# --- Ativos americanos ---
df_usa = df_exibir[~df_exibir["TickerYF"].str.endswith(".SA", na=False)]

st.subheader("Carteira Atual vs Alocação Ideal – Ativos Americanos")
st.dataframe(df_usa[["Produto", "Valor Aplicado", "Saldo Bruto",
                     "Participação Atual", "Participação Ideal",
                     "Diferença", "Status", "ValorAtual", "Desconto (%)"]])
