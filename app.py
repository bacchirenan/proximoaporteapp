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
# Conferir colunas
# ============================
st.write("Colunas Carteira:", df_carteira.columns.tolist())
st.write("Colunas Alocacao:", df_alocacao.columns.tolist())

# ============================
# Renomear colunas para nomes consistentes
# ============================
df_carteira = df_carteira.rename(columns={
    "Produto": "Ativo",
    "Data da primeira aplicação": "Data",
    "Valor aplicado": "ValorAplicado",
    "Saldo bruto": "SaldoBruto",
    "Rentabilidade (%)": "Rentabilidade",
    "Participação na carteira (%)": "ParticipacaoAtual"
})

df_alocacao = df_alocacao.rename(columns={
    "Ativo": "Ativo",
    "PercentualIdeal": "ParticipacaoIdeal"
})

# ============================
# Converter texto em número
# ============================
for col in ["ParticipacaoAtual"]:
    if col in df_carteira.columns:
        df_carteira[col] = (
            df_carteira[col].astype(str)
            .str.replace("%", "")
            .str.replace(",", ".")
        )
        df_carteira[col] = pd.to_numeric(df_carteira[col], errors="coerce")
    else:
        st.error(f"❌ Coluna '{col}' não encontrada na aba Carteira.")
        st.stop()

for col in ["ParticipacaoIdeal"]:
    if col in df_alocacao.columns:
        df_alocacao[col] = (
            df_alocacao[col].astype(str)
            .str.replace("%", "")
            .str.replace(",", ".")
        )
        df_alocacao[col] = pd.to_numeric(df_alocacao[col], errors="coerce")
    else:
        st.error(f"❌ Coluna '{col}' não encontrada na aba Alocacao.")
        st.stop()

# ============================
# Merge Carteira x Alocacao
# ============================
df = pd.merge(df_carteira, df_alocacao, on="Ativo", how="outer")

# ============================
# Consolidar ativos repetidos
# ============================
df = df.groupby("Ativo", as_index=False).agg({
    "Data": "min",                  # primeira alocação
    "ValorAplicado": "sum",         # soma de valores aplicados
    "SaldoBruto": "sum",            # soma de saldos brutos
    "Rentabilidade": "mean",        # média da rentabilidade
    "ParticipacaoAtual": "sum",     # soma da participação atual
    "ParticipacaoIdeal": "mean"     # média da alocação ideal
})

# Recalcular diferença
df["Diferenca"] = df["ParticipacaoIdeal"] - df["ParticipacaoAtual"]

# ============================
# Interface
# ============================
st.title("📊 Gestão de Carteira")

st.subheader("Carteira atual vs Alocação ideal (Consolidada)")
st.dataframe(df, use_container_width=True)

# Resumo com cores
st.subheader("Resumo")
for _, row in df.iterrows():
    if row["Diferenca"] > 0:
        st.write(f"🔵 Comprar mais de **{row['Ativo']}** (+{row['Diferenca']:.2f}%)")
    elif row["Diferenca"] < 0:
        st.write(f"🔴 Reduzir posição em **{row['Ativo']}** ({row['Diferenca']:.2f}%)")
    else:
        st.write(f"✅ {row['Ativo']} já está na alocação ideal.")
