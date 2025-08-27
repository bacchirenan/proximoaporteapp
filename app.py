import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import re

st.set_page_config(page_title="Gestão de Carteira", layout="wide")

# -------------------------
# Helpers
# -------------------------
def extract_spreadsheet_id(url_or_id: str) -> str:
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", str(url_or_id))
    return m.group(1) if m else str(url_or_id)

def parse_percent_col(series: pd.Series) -> pd.Series:
    # aceita valores como "12,3%", "12.3", "12,3" ou números
    s = series.fillna(0).astype(str).str.replace('%', '', regex=False).str.replace(' ', '')
    s = s.str.replace(',', '.', regex=False)
    return pd.to_numeric(s, errors='coerce').fillna(0.0)

# -------------------------
# Verifica secrets
# -------------------------
if "gcp_service_account" not in st.secrets:
    st.error("Não encontrei `st.secrets['gcp_service_account']`. Adicione as credenciais do Service Account nos Secrets do Streamlit Cloud.")
    st.stop()

raw_creds = st.secrets["gcp_service_account"]
service_account_info = None

# tenta interpretar st.secrets em vários formatos
try:
    if isinstance(raw_creds, dict):
        # caso ideal: já é dict com chaves do JSON
        service_account_info = raw_creds
    elif isinstance(raw_creds, str):
        # se for string JSON
        service_account_info = json.loads(raw_creds)
    else:
        # caso raro: tentamos converter
        service_account_info = json.loads(json.dumps(raw_creds))
except Exception:
    # às vezes o secret vem com nested key "json"
    try:
        if isinstance(raw_creds, dict) and "json" in raw_creds:
            service_account_info = json.loads(raw_creds["json"])
    except Exception as e:
        st.error("Falha ao interpretar as credenciais do Service Account (formato inválido).")
        st.exception(e)
        st.stop()

if not isinstance(service_account_info, dict):
    st.error("Erro: `service_account_info` não pôde ser reconstruído como dicionário. Verifique o formato em st.secrets.")
    st.stop()

# -------------------------
# Cria credenciais e cliente gspread
# -------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
except Exception as e:
    st.error("Erro ao criar Credentials a partir do service account info.")
    st.exception(e)
    st.stop()

service_email = service_account_info.get("client_email", "<client_email não encontrado>")
st.info("Service account (copie este e-mail para compartilhar a planilha):")
st.code(service_email)

try:
    gc = gspread.authorize(creds)
except Exception as e:
    st.error("Erro ao autorizar gspread com as credenciais fornecidas.")
    st.exception(e)
    st.stop()

# -------------------------
# Obtém URL/ID da planilha
# -------------------------
SPREADSHEET_URL = st.secrets.get("spreadsheet_url") or st.secrets.get("spreadsheet_id")
if not SPREADSHEET_URL:
    st.error("Defina `st.secrets['spreadsheet_url']` (ou 'spreadsheet_id') com a URL ou ID da planilha.")
    st.stop()

spreadsheet_id = extract_spreadsheet_id(SPREADSHEET_URL)
st.write("Planilha alvo (ID):", spreadsheet_id)

# tenta abrir a planilha e dá instruções claras se der PermissionError
try:
    sh = gc.open_by_url(SPREADSHEET_URL) if "http" in str(SPREADSHEET_URL) else gc.open_by_key(spreadsheet_id)
except PermissionError as e:
    st.error("PermissionError: o Service Account **não tem acesso** à planilha.")
    st.markdown(
        "- Abra a planilha no Google Sheets → **Compartilhar** → adicione o e-mail do Service Account abaixo e dê permissão **Editor** (ou Leitor se for só leitura)."
    )
    st.code(service_email)
    st.markdown(f"- Verifique também que você está compartilhando a planilha correta (ID: `{spreadsheet_id}`).")
    st.stop()
except Exception as e:
    st.error("Erro ao abrir a planilha (não é necessariamente de permissão). Veja o erro abaixo:")
    st.exception(e)
    st.stop()

# -------------------------
# Carregar abas e tratar colunas
# -------------------------
try:
    ws_carteira = sh.worksheet("Carteira")
    df_carteira = pd.DataFrame(ws_carteira.get_all_records())
except Exception as e:
    st.error("Erro ao carregar a aba 'Carteira'. Verifique se existe uma aba chamada exatamente 'Carteira'.")
    st.exception(e)
    st.stop()

try:
    ws_alocacao = sh.worksheet("Alocacao")
    df_alocacao = pd.DataFrame(ws_alocacao.get_all_records())
except Exception as e:
    st.error("Erro ao carregar a aba 'Alocacao'. Verifique se existe uma aba chamada exatamente 'Alocacao'.")
    st.exception(e)
    st.stop()

# Normaliza nomes das colunas conforme sua especificação
# Esperado:
#   Carteira: Produto ; Participação na carteira (%)
#   Alocacao: Ativo ; PercentualIdeal

# Rename Carteira
rename_map_carteira = {}
if "Produto" in df_carteira.columns:
    rename_map_carteira["Produto"] = "Ativo"
else:
    st.warning("Coluna 'Produto' não encontrada na aba Carteira — verifique o nome da coluna.")

if "Participação na carteira (%)" in df_carteira.columns:
    rename_map_carteira["Participação na carteira (%)"] = "PercentualAtual"
else:
    # tenta detectar variações comuns
    for col in df_carteira.columns:
        if "participa" in col.lower() or "participa" in col:
            rename_map_carteira[col] = "PercentualAtual"
            break

df_carteira.rename(columns=rename_map_carteira, inplace=True)

# Rename Alocacao
rename_map_alocacao = {}
if "Ativo" in df_alocacao.columns:
    rename_map_alocacao["Ativo"] = "Ativo"
else:
    st.warning("Coluna 'Ativo' não encontrada na aba Alocacao — verifique o nome da coluna.")

if "PercentualIdeal" in df_alocacao.columns:
    rename_map_alocacao["PercentualIdeal"] = "PercentualIdeal"
else:
    for col in df_alocacao.columns:
        if "ideal" in col.lower():
            rename_map_alocacao[col] = "PercentualIdeal"
            break

df_alocacao.rename(columns=rename_map_alocacao, inplace=True)

# Garante colunas existam
if "Ativo" not in df_carteira.columns or "PercentualAtual" not in df_carteira.columns:
    st.error("Aba 'Carteira' precisa das colunas: 'Produto' e 'Participação na carteira (%)' (ou nomes equivalentes).")
    st.stop()
if "Ativo" not in df_alocacao.columns or "PercentualIdeal" not in df_alocacao.columns:
    st.error("Aba 'Alocacao' precisa das colunas: 'Ativo' e 'PercentualIdeal' (ou nomes equivalentes).")
    st.stop()

# Converte percentuais para float
df_carteira["PercentualAtual"] = parse_percent_col(df_carteira["PercentualAtual"])
df_alocacao["PercentualIdeal"] = parse_percent_col(df_alocacao["PercentualIdeal"])

# Merge e cálculo
df_resultado = pd.merge(df_carteira[["Ativo", "PercentualAtual"]],
                        df_alocacao[["Ativo", "PercentualIdeal"]],
                        on="Ativo", how="outer")

df_resultado["PercentualAtual"] = df_resultado["PercentualAtual"].fillna(0.0)
df_resultado["PercentualIdeal"] = df_resultado["PercentualIdeal"].fillna(0.0)
df_resultado["Diferenca (%)"] = df_resultado["PercentualAtual"] - df_resultado["PercentualIdeal"]

# Exibição
st.title("Gestão de Carteira")
st.subheader("Carteira (raw)")
st.dataframe(df_carteira)

st.subheader("Alocação Ideal (raw)")
st.dataframe(df_alocacao)

st.subheader("Comparação Atual x Ideal")
st.dataframe(df_resultado.sort_values("Diferenca (%)", ascending=False))

# Gráfico simples (barra) comparando Atual x Ideal
st.subheader("Gráfico — Atual vs Ideal")
st.bar_chart(df_resultado.set_index("Ativo")[["PercentualAtual", "PercentualIdeal"]])
