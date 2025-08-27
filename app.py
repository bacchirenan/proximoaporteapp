import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

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

# ==== Testa o acesso ====
worksheet = sh.sheet1  # pega a primeira aba
data = worksheet.get_all_records()
st.write("Dados da planilha:", data)
