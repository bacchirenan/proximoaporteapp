import streamlit as st
import pandas as pd

# ====== CONFIGURAÇÕES DA PÁGINA ======
st.set_page_config(page_title="Gestão de Carteira", layout="wide")

# ====== URLs DOS CSVs EXPORTADOS DO GOOGLE SHEETS ======
URL_CARTEIRA = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=0"
URL_ALOCACAO = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=123456789"  
# 👉 substitua o gid pelo da aba Alocacao

# ====== LEITURA DOS DADOS ======
try:
    df_carteira = pd.read_csv(URL_CARTEIRA)
    df_alocacao = pd.read_csv(URL_ALOCACAO)
except Exception as e:
    st.error("Erro ao carregar os dados da planilha. Verifique as permissões de compartilhamento (qualquer pessoa com link).")
    st.stop()

# Renomeia colunas para consistência
df_carteira.rename(columns={
    "Produto": "Ativo",
    "Participação na carteira (%)": "PercentualAtual"
}, inplace=True)

df_alocacao.rename(columns={
    "Ativo": "Ativo",
    "PercentualIdeal": "PercentualIdeal"
}, inplace=True)

# ====== PROCESSAMENTO ======
df_merged = pd.merge(df_carteira, df_alocacao, on="Ativo", how="outer").fillna(0)
df_merged["Diferença"] = df_merged["PercentualAtual"] - df_merged["PercentualIdeal"]

# ====== INTERFACE ======
st.title("📊 Gestão de Carteira")

st.subheader("Resumo da Carteira vs Alocação Ideal")
st.dataframe(df_merged, use_container_width=True)

# Gráfico comparativo
st.subheader("Distribuição Atual vs Ideal")
st.bar_chart(
    df_merged.set_index("Ativo")[["PercentualAtual", "PercentualIdeal"]]
)
