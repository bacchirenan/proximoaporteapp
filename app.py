import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Gestão de Carteira", layout="wide")
st.title("Gestão de Carteira")

# URLs das planilhas CSV públicas
URL_CARTEIRA = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FR1bFsliZ3DFH0W7sFfZZ8Xo/pub?gid=0&single=true&output=csv"

# Função para buscar cotações
@st.cache_data(ttl=300)
def get_cotacao(ticker):
    try:
        ticker_data = yf.Ticker(ticker)
        return ticker_data.history(period="1d")["Close"].iloc[-1]
    except:
        return None

# Carregar dados
df = pd.read_csv(URL_CARTEIRA)

# Normalização de colunas
df["ValorAplicado"] = df["ValorAplicado"].replace("[R$]", "", regex=True).astype(float)
df["SaldoBruto"] = df["SaldoBruto"].replace("[R$]", "", regex=True).astype(float)

# Buscar valor atual (cotação)
df["ValorAtual"] = df["Ticker"].apply(lambda x: get_cotacao(x))
df["ValorAtual"] = df["ValorAtual"].map(lambda x: f"R${x:,.2f}" if x is not None else "N/A")

# Ajustar colunas de participação
df["Participação Atual"] = df["Participação Atual"].astype(str) + "%"
df["Participação Ideal"] = df["Participação Ideal"].astype(str) + "%"
df["Diferenca"] = df["Diferenca"].astype(str) + "%"

# Separar categorias
df_acoes = df[df["Categoria"] == "Ações Nacionais"]
df_fiis = df[df["Categoria"] == "FIIs"]
df_usa = df[df["Categoria"] == "Ativos Americanos"]
df_aporte = df[df["Categoria"] == "Recomendação Aporte"]

# Exibir tabelas
st.subheader("Carteira Atual vs Alocação Ideal – Ações Nacionais")
st.table(df_acoes[["Produto", "Valor Aplicado", "Saldo Bruto",
                   "Participação Atual", "Participação Ideal",
                   "Diferenca", "Status", "ValorAtual"]].rename(columns={"ValorAtual": "Valor Atual"}))

st.subheader("Carteira Atual vs Alocação Ideal – FIIs")
st.table(df_fiis[["Produto", "Valor Aplicado", "Saldo Bruto",
                  "Participação Atual", "Participação Ideal",
                  "Diferenca", "Status", "ValorAtual"]].rename(columns={"ValorAtual": "Valor Atual"}))

st.subheader("Carteira Atual vs Alocação Ideal – Ativos Americanos")
st.table(df_usa[["Produto", "Valor Aplicado", "Saldo Bruto",
                 "Participação Atual", "Participação Ideal",
                 "Diferenca", "Status", "ValorAtual"]].rename(columns={"ValorAtual": "Valor Atual"}))

st.subheader("Recomendações de Aporte")
st.table(df_aporte[["Produto", "Valor Aplicado", "Saldo Bruto",
                    "Participação Atual", "Participação Ideal",
                    "Diferenca", "Status", "ValorAtual"]].rename(columns={"ValorAtual": "Valor Atual"}))
