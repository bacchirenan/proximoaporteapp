import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

service_account_info = st.secrets["gcp_service_account"]
scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
gc = gspread.authorize(credentials)

# Teste de abertura
try:
    sh = gc.open_by_key("1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74")
    st.success("Planilha aberta com sucesso!")
except Exception as e:
    st.error(f"Erro ao abrir a planilha: {e}")
