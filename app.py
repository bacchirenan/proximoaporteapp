import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Gestão de Carteira", layout="wide")
st.title("Gestão de Carteira")

# URL corrigida para exportação CSV
URL_CARTEIRA = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=0"

# Carregar dados da carteira
df_carteira = pd.read_csv(URL_CARTEIRA)

# Garantir que as colunas necessárias existam
colunas_necessarias = ["Produto", "Ticker", "Classe", "Valor Aplicado", "Participação Ideal"]
for col in colunas_necessarias:
    if col not in df_carteira.columns:
        st.error(f"Coluna ausente na planilha: {col}")
        st.stop()

# Buscar cotações atuais
df_carteira["Valor Atual"] = 0.0
for i, row in df_carteira.iterrows():
    ticker = str(row["Ticker"]).strip()
    try:
        dados = yf.Ticker(ticker).history(period="1d")
        if not dados.empty:
            preco = dados["Close"].iloc[-1]
            df_carteira.at[i, "Valor Atual"] = preco
    except Exception as e:
        st.warning(f"Não foi possível buscar cotação de {ticker}: {e}")

# Calcular valor total investido
valor_total = df_carteira["Valor Aplicado"].sum()

# Calcular participação atual
df_carteira["Participação Atual"] = df_carteira["Valor Aplicado"] / valor_total * 100

# Corrigir Participação Ideal nula ou inválida
df_carteira["Participação Ideal"] = pd.to_numeric(df_carteira["Participação Ideal"], errors="coerce").fillna(0)

# Diferença entre ideal e atual
df_carteira["Diferença"] = df_carteira["Participação Ideal"] - df_carteira["Participação Atual"]

# Definir status
def definir_status(diff):
    if diff > 0.5:
        return "Comprar mais"
    elif diff < -0.5:
        return "Excesso"
    else:
        return "Ok"

df_carteira["Status"] = df_carteira["Diferença"].apply(definir_status)

# Exibir tabela
st.subheader("Resumo da Carteira")
st.dataframe(df_carteira)

# Ativos mais descontados
st.subheader("Ativos mais descontados")
mais_descontados = df_carteira.sort_values(by="Diferença", ascending=False).head(5)
st.dataframe(mais_descontados)

# Ativos em status 'Comprar mais'
st.subheader("Ativos em status 'Comprar mais'")
comprar_mais = df_carteira[df_carteira["Status"] == "Comprar mais"]
st.dataframe(comprar_mais)
