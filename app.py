import streamlit as st
import pandas as pd
import re

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

# ------------------------------
# Função para limpar valores monetários
# ------------------------------
def parse_valor(valor):
    if pd.isna(valor):
        return 0
    # Remove tudo que não seja número, vírgula ou ponto
    valor = re.sub(r"[^\d,.-]", "", str(valor))
    # Troca vírgula por ponto
    valor = valor.replace(",", ".")
    try:
        return float(valor)
    except:
        return 0

# Aplicar limpeza
df_carteira["ValorAplicado"] = df_carteira["Valor aplicado"].apply(parse_valor)
df_carteira["SaldoBruto"] = df_carteira["Saldo bruto"].apply(parse_valor)
df_carteira["ParticipacaoAtual"] = df_carteira["Participação na carteira (%)"].apply(parse_valor)

# Agrupar ativos repetidos
df_carteira = df_carteira.groupby("Produto", as_index=False).agg({
    "ValorAplicado": "sum",
    "SaldoBruto": "sum",
    "ParticipacaoAtual": "sum"
})

# ------------------------------
# Preparar Alocacao
# ------------------------------
df_alocacao = df_alocacao.rename(columns={"Ativo": "Produto", "PercentualIdeal": "ParticipacaoIdeal"})
df_alocacao["ParticipacaoIdeal"] = df_alocacao["ParticipacaoIdeal"].apply(parse_valor)

# Merge Carteira x Alocacao
df = pd.merge(df_carteira, df_alocacao, on="Produto", how="outer")

# Preencher zeros
for col in ["ValorAplicado", "SaldoBruto", "ParticipacaoAtual", "ParticipacaoIdeal"]:
    df[col] = df[col].fillna(0)

# Calcular diferença
df["Diferenca"] = df["ParticipacaoIdeal"] - df["ParticipacaoAtual"]

# Mostrar apenas colunas essenciais
df_display = df[["Produto", "ValorAplicado", "SaldoBruto", "ParticipacaoAtual", "ParticipacaoIdeal", "Diferenca"]]

# ------------------------------
# Exibir tabela
# ------------------------------
st.title("📊 Carteira vs Alocação Ideal")
st.dataframe(df_display, use_container_width=True)

# ------------------------------
# Resumo colorido
# ------------------------------
st.subheader("Resumo")
for _, row in df_display.iterrows():
    if row["Diferenca"] > 0:
        st.write(f"🔵 Comprar mais de **{row['Produto']}** (+{row['Diferenca']:.2f}%)")
    elif row["Diferenca"] < 0:
        st.write(f"🔴 Reduzir posição em **{row['Produto']}** ({row['Diferenca']:.2f}%)")
    else:
        st.write(f"✅ {row['Produto']} já está na alocação ideal.")
