import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

import streamlit as st

st.write("Service account email:", st.secrets["gcp_service_account"]["client_email"])

# ==== Carrega credenciais do secrets.toml ====
service_account_info = st.secrets["gcp_service_account"]

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
gc = gspread.authorize(credentials)

# ==== Abre a planilha ====
SPREADSHEET_URL = st.secrets["gcp_service_account"]["spreadsheet_url"]
sh = gc.open_by_url(SPREADSHEET_URL)

# ==== Lê aba Carteira ====
try:
    carteira_sheet = sh.worksheet("Carteira")
    carteira_data = carteira_sheet.get_all_records()
    df_carteira = pd.DataFrame(carteira_data)
    st.subheader("Aba: Carteira")
    st.dataframe(df_carteira)
except gspread.WorksheetNotFound:
    st.error("A aba 'Carteira' não foi encontrada na planilha.")

# ==== Lê aba Alocacao ====
try:
    alocacao_sheet = sh.worksheet("Alocacao")
    alocacao_data = alocacao_sheet.get_all_records()
    df_alocacao = pd.DataFrame(alocacao_data)
    st.subheader("Aba: Alocacao")
    st.dataframe(df_alocacao)
except gspread.WorksheetNotFound:
    st.error("A aba 'Alocacao' não foi encontrada na planilha.")

# ==== Exemplo de uso: cruzar informações ====
if 'Produto' in df_carteira.columns and 'Ativo' in df_alocacao.columns:
    merged = pd.merge(df_carteira, df_alocacao, left_on="Produto", right_on="Ativo", how="left")
    st.subheader("Carteira com Alocação Ideal")
    st.dataframe(merged)

