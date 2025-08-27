import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ===== Configuração da página =====
st.set_page_config(page_title="Gestão de Carteira", layout="wide")

# ===== Conectar ao Google Sheets =====
# Credenciais do service account (no secrets do Streamlit Cloud)
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.authorize(creds)

# ===== URL da planilha =====
SPREADSHEET_URL = st.secrets["spreadsheet_url"]

# Abrir a planilha
sh = gc.open_by_url(SPREADSHEET_URL)

# Carregar aba "Carteira"
ws_carteira = sh.worksheet("Carteira")
df_carteira = pd.DataFrame(ws_carteira.get_all_records())

# Carregar aba "Alocacao"
ws_alocacao = sh.worksheet("Alocacao")
df_alocacao = pd.DataFrame(ws_alocacao.get_all_records())

# ===== Processar os dados =====
# Normaliza nomes das colunas
df_carteira.rename(columns={
    "Produto": "Ativo",
    "Participação na carteira (%)": "PercentualAtual"
}, inplace=True)

df_alocacao.rename(columns={
    "Ativo": "Ativo",
    "PercentualIdeal": "PercentualIdeal"
}, inplace=True)

# Unir as duas tabelas pelo nome do ativo
df_resultado = pd.merge(
    df_carteira,
    df_alocacao,
    on="Ativo",
    how="outer"
)

# Calcular diferença entre alocação atual e ideal
df_resultado["Diferença (%)"] = df_resultado["PercentualAtual"].fillna(0) - df_resultado["PercentualIdeal"].fillna(0)

# ===== Exibir no Streamlit =====
st.title("Gestão de Carteira")

st.subheader("Carteira Atual")
st.dataframe(df_carteira)

st.subheader("Alocação Ideal")
st.dataframe(df_alocacao)

st.subheader("Comparação")
st.dataframe(df_resultado)
