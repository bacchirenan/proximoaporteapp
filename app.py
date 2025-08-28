import streamlit as st
import pandas as pd

st.set_page_config(page_title="Carteira vs Alocação", layout="wide")

# URLs públicas CSV
URL_CARTEIRA = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=0"
URL_ALOCACAO = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=1042665035"

# Carregar dados
try:
    df_carteira = pd.read_csv(URL_CARTEIRA)
    df_alocacao = pd.read_csv(URL_ALOCACAO)
except Exception:
    st.error("❌ Erro ao carregar os dados da planilha. Verifique se o link está público.")
    st.stop()

# Preparar Carteira
df_carteira["ValorAplicado"] = pd.to_numeric(df_carteira["Valor aplicado"], errors="coerce").fillna(0)
df_carteira["SaldoBruto"] = pd.to_numeric(df_carteira["Saldo bruto"], errors="coerce").fillna(0)
df_carteira["ParticipacaoAtual"] = (
    df_carteira["Participação na carteira (%)"].astype(str)
    .str.replace(",", ".")
    .str.replace("%", "")
)
df_carteira["ParticipacaoAtual"] = pd.to_numeric(df_carteira["ParticipacaoAtual"], errors="coerce").fillna(0)

# Agrupar ativos repetidos
df_carteira = df_carteira.groupby("Produto", as_index=False).agg({
    "ValorAplicado": "sum",
    "SaldoBruto": "sum",
    "ParticipacaoAtual": "sum"
})

# Preparar Alocacao
df_alocacao = df_alocacao.rename(columns={"Ativo": "Produto", "PercentualIdeal": "ParticipacaoIdeal"})
df_alocacao["ParticipacaoIdeal"] = (
    df_alocacao["ParticipacaoIdeal"].astype(str).str.replace(",", ".")
)
df_alocacao["ParticipacaoIdeal"] = pd.to_numeric(df_alocacao["ParticipacaoIdeal"], errors="coerce").fillna(0)

# Merge Carteira x Alocacao
df = pd.merge(df_carteira, df_alocacao, on="Produto", how="outer")

# Preencher zeros
for col in ["ValorAplicado", "SaldoBruto", "ParticipacaoAtual", "ParticipacaoIdeal"]:
    df[col] = df[col].fillna(0)

# Calcular diferença
df["Diferenca"] = df["ParticipacaoIdeal"] - df["ParticipacaoAtual"]

# Mostrar apenas colunas essenciais
df_display = df[["Produto", "ValorAplicado", "SaldoBruto", "ParticipacaoAtual", "ParticipacaoIdeal", "Diferenca"]]

# Exibir tabela
st.title("📊 Carteira vs Alocação Ideal")
st.dataframe(df_display, use_container_width=True)

# Resumo colorido
st.subheader("Resumo")
for _, row in df_display.iterrows():
    if row["Diferenca"] > 0:
        st.write(f"🔵 Comprar mais de **{row['Produto']}** (+{row['Diferenca']:.2f}%)")
    elif row["Diferenca"] < 0:
        st.write(f"🔴 Reduzir posição em **{row['Produto']}** ({row['Diferenca']:.2f}%)")
    else:
        st.write(f"✅ {row['Produto']} já está na alocação ideal.")
