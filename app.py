import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Gestão de Carteira (CSV público)", layout="wide")

# =========================
# Helpers
# =========================
def extract_sheet_id(url_or_id: str) -> str:
    """Extrai o ID da planilha a partir de uma URL completa ou retorna o próprio valor se já for um ID."""
    if not url_or_id:
        return ""
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", str(url_or_id))
    return m.group(1) if m else str(url_or_id).strip()

def csv_export_url(sheet_id: str, gid: str | int) -> str:
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

def parse_percent_col(series: pd.Series) -> pd.Series:
    """Aceita '12,3%', '12.3', '12,3', 12.3 etc., converte para float (em %)"""
    s = series.astype(str).str.strip()
    s = s.str.replace("%", "", regex=False).str.replace(" ", "", regex=False)
    s = s.str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

@st.cache_data(ttl=60)
def load_csv_as_df(url: str) -> pd.DataFrame:
    # Lê CSV público. Se a planilha não estiver pública, o conteúdo pode ser HTML; o pandas vai quebrar.
    df = pd.read_csv(url, on_bad_lines="skip")
    return df

# =========================
# Inputs (você pode preencher via UI ou via st.secrets)
# =========================
default_sheet = st.secrets.get("sheet_id", "")
default_gid_carteira = str(st.secrets.get("gid_carteira", "")) or ""
default_gid_alocacao = str(st.secrets.get("gid_alocacao", "")) or ""

st.title("Gestão de Carteira — Google Sheets (CSV público)")

with st.expander("Configurar planilha (cole a URL ou o ID + gids)"):
    sheet_url_or_id = st.text_input("URL completa da planilha OU apenas o ID",
                                    value=default_sheet,
                                    placeholder="Ex.: https://docs.google.com/spreadsheets/d/XXXX/edit#gid=0  OU  XXXX")
    gid_carteira = st.text_input("gid da aba 'Carteira'",
                                 value=default_gid_carteira,
                                 placeholder="Ex.: 0 ou 123456789")
    gid_alocacao = st.text_input("gid da aba 'Alocacao'",
                                 value=default_gid_alocacao,
                                 placeholder="Ex.: 987654321")

sheet_id = extract_sheet_id(sheet_url_or_id)

if not sheet_id or not gid_carteira or not gid_alocacao:
    st.warning("Preencha a URL/ID da planilha e os dois gids (Carteira e Alocacao).")
    st.stop()

# =========================
# Monta URLs CSV e carrega
# =========================
url_carteira = csv_export_url(sheet_id, gid_carteira)
url_alocacao = csv_export_url(sheet_id, gid_alocacao)

col_urls = st.columns(2)
with col_urls[0]:
    st.caption("CSV Carteira")
    st.code(url_carteira, language="text")
with col_urls[1]:
    st.caption("CSV Alocacao")
    st.code(url_alocacao, language="text")

try:
    df_carteira_raw = load_csv_as_df(url_carteira)
    df_alocacao_raw = load_csv_as_df(url_alocacao)
except Exception as e:
    st.error("Falha ao baixar CSV. Verifique se a planilha está com acesso **Qualquer pessoa com o link → Leitor** e se os **gids** estão corretos.")
    st.exception(e)
    st.stop()

if df_carteira_raw.empty or df_alocacao_raw.empty:
    st.error("Uma das abas veio vazia. Confira se o gid está certo e se há dados.")
    st.stop()

# =========================
# Normalização de colunas
# =========================
# Renomeia Carteira: Produto -> Ativo ; Participação na carteira (%) -> PercentualAtual
df_carteira = df_carteira_raw.copy()
rename_map_carteira = {}
# Tenta encontrar colunas mesmo com variações (acentos, espaços)
def find_col(df, targets):
    lower = {c.lower(): c for c in df.columns}
    for t in targets:
        if t.lower() in lower:
            return lower[t.lower()]
    # fallback: contém parte do nome
    for c in df.columns:
        cl = c.lower()
        if any(t.lower() in cl for t in targets):
            return c
    return None

col_produto = find_col(df_carteira, ["Produto"])
col_part = find_col(df_carteira, ["Participação na carteira (%)", "Participacao na carteira (%)", "Participação", "Participacao"])
if not col_produto or not col_part:
    st.error("A aba **Carteira** precisa ter as colunas 'Produto' e 'Participação na carteira (%)'.")
    st.stop()

rename_map_carteira[col_produto] = "Ativo"
rename_map_carteira[col_part] = "PercentualAtual"
df_carteira = df_carteira.rename(columns=rename_map_carteira)[["Ativo", "PercentualAtual"]]
df_carteira["PercentualAtual"] = parse_percent_col(df_carteira["PercentualAtual"])

# Renomeia Alocacao: Ativo ; PercentualIdeal
df_alocacao = df_alocacao_raw.copy()
col_ativo = find_col(df_alocacao, ["Ativo"])
col_ideal = find_col(df_alocacao, ["PercentualIdeal", "Ideal"])
if not col_ativo or not col_ideal:
    st.error("A aba **Alocacao** precisa ter as colunas 'Ativo' e 'PercentualIdeal'.")
    st.stop()

df_alocacao = df_alocacao.rename(columns={col_ativo: "Ativo", col_ideal: "PercentualIdeal"})[["Ativo", "PercentualIdeal"]]
df_alocacao["PercentualIdeal"] = parse_percent_col(df_alocacao["PercentualIdeal"])

# =========================
# Merge + cálculo
# =========================
df = pd.merge(df_carteira, df_alocacao, on="Ativo", how="outer")
df["PercentualAtual"] = df["PercentualAtual"].fillna(0.0)
df["PercentualIdeal"] = df["PercentualIdeal"].fillna(0.0)
df["Diferenca (%)"] = df["PercentualAtual"] - df["PercentualIdeal"]

# =========================
# Exibição
# =========================
st.subheader("Carteira (aba 'Carteira')")
st.dataframe(df_carteira)

st.subheader("Alocação Ideal (aba 'Alocacao')")
st.dataframe(df_alocacao)

st.subheader("Comparação — Atual x Ideal")
st.dataframe(df.sort_values("Diferenca (%)", ascending=False), use_container_width=True)

st.subheader("Gráfico — Atual vs Ideal")
st.bar_chart(df.set_index("Ativo")[["PercentualAtual", "PercentualIdeal"]])

# Infos úteis
with st.expander("Dicas & Validações"):
    soma_atual = df["PercentualAtual"].sum()
    soma_ideal = df["PercentualIdeal"].sum()
    st.write(f"Soma dos percentuais — **Atual**: {soma_atual:.2f}% | **Ideal**: {soma_ideal:.2f}%")
    if abs(soma_atual - 100) > 0.5:
        st.warning("A soma da **Carteira Atual** não é ~100%. Verifique se os percentuais estão corretos.")
    if abs(soma_ideal - 100) > 0.5:
        st.warning("A soma da **Alocação Ideal** não é ~100%. Verifique se os percentuais estão corretos.")
