import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Gestão de Carteira", layout="wide")
st.title("Gestão de Carteira")

# URLs das planilhas CSV públicas
URL_CARTEIRA = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=0"
URL_ALOCACAO = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=1042665035"

# Carregar dados
try:
    df_carteira = pd.read_csv(URL_CARTEIRA)
    df_alocacao = pd.read_csv(URL_ALOCACAO)
except Exception as e:
    st.error("Erro ao carregar os dados da planilha. Verifique o link e permissões.")
    st.stop()

# Padronizar nomes de colunas removendo espaços extras
df_carteira.columns = df_carteira.columns.str.strip()
df_alocacao.columns = df_alocacao.columns.str.strip()

# Substituir vírgula por ponto e converter para numérico de forma segura
numericas = ["Valor aplicado", "Saldo bruto", "Rentabilidade (%)", "Participação na carteira (%)"]
for col in numericas:
    df_carteira[col] = pd.to_numeric(
        df_carteira[col].astype(str).str.replace(",", ".").str.strip(),
        errors="coerce"
    )

df_alocacao["PercentualIdeal"] = pd.to_numeric(
    df_alocacao["PercentualIdeal"].astype(str).str.replace(",", ".").str.strip(),
    errors="coerce"
)

# Agrupar Carteira por Produto
df_carteira = df_carteira.groupby("Produto", as_index=False).agg({
    "Valor aplicado": "sum",
    "Saldo bruto": "sum",
    "Rentabilidade (%)": "mean",
    "Participação na carteira (%)": "sum"
})

# Renomear colunas para padronizar
df_carteira.rename(columns={
    "Valor aplicado": "ValorAplicado",
    "Saldo bruto": "SaldoBruto",
    "Rentabilidade (%)": "Rentabilidade",
    "Participação na carteira (%)": "ParticipacaoAtual"
}, inplace=True)
df_alocacao.rename(columns={"PercentualIdeal": "ParticipacaoIdeal", "Ativo": "Produto"}, inplace=True)

# Merge Carteira + Alocacao
df = pd.merge(df_carteira, df_alocacao, on="Produto", how="left")

# Calcular diferença e status
df["Diferenca"] = df["ParticipacaoIdeal"] - df["ParticipacaoAtual"]

def status(row):
    if pd.isna(row["Diferenca"]):
        return "—"
    elif row["Diferenca"] > 0:
        return "Comprar mais"
    elif row["Diferenca"] < 0:
        return "Reduzir"
    else:
        return "Ok"

df["Status"] = df.apply(status, axis=1)

# Buscar valor atual online
def get_valor_atual(ticker):
    try:
        ticker_data = yf.Ticker(ticker.split(" - ")[0])
        price = ticker_data.history(period="1d")["Close"][-1]
        return price
    except:
        return None

df["ValorAtual"] = df["Produto"].apply(get_valor_atual)

# Formatar valores monetários
df["ValorApli]()
