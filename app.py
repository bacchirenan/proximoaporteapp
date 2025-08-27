import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestão de Carteira", layout="wide")

# ============================
# URLs das planilhas públicas (CSV export)
# ============================
URL_CARTEIRA = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=0"
URL_ALOCACAO = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=1042665035"

# ============================
# Carregar dados
# ============================
try:
    df_carteira = pd.read_csv(URL_CARTEIRA)
    df_alocacao = pd.read_csv(URL_ALOCACAO)
except Exception as e:
    st.error("❌ Erro ao carregar os dados da planilha. Verifique se o link está acessível ao público (qualquer pessoa com link).")
    st.stop()

# ============================
# Processar dados
# ============================
df_carteira = df_carteira.rename(columns={
    "Produto": "Ativo",
    "Participação na carteira (%)": "ParticipacaoAtual"
})

df_alocacao = df_alocacao.rename(columns={
    "Ativo": "Ativo",
    "PercentualIdeal": "ParticipacaoIdeal"
})

# Juntar os dois
df = pd.merge(df_carteira, df_alocacao, on="Ativo", how="outer")

# Calcular diferença
df["Diferenca"] = df["ParticipacaoIdeal"] - df["ParticipacaoAtual"]

# ============================
# Interface
# ============================
st.title("📊 Gestão de Carteira")

st.subheader("Carteira Atual vs Alocação Ideal")
st.dataframe(df, use_container_width=True)

st.subheader("Resumo")
for _, row in df.iterrows():
    if row["Diferenca"] > 0:
        st.write(f"➡️ Comprar mais de **{row['Ativo']}** (+{row['Diferenca']:.2f}%)")
    elif row["Diferenca"] < 0:
        st.write(f"⬅️ Reduzir posição em **{row['Ativo']}** ({row['Diferenca']:.2f}%)")
    else:
        st.write(f"✅ {row['Ativo']} já está na alocação ideal.")
