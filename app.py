import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Gestão de Carteira", layout="wide")

# --- URLs CSV público ---
URL_CARTEIRA = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=0"
URL_ALOCACAO = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=1042665035"

# --- Carregar dados ---
df_carteira = pd.read_csv(URL_CARTEIRA)
df_alocacao = pd.read_csv(URL_ALOCACAO)

# --- Agrupar Carteira por Produto ---
df_carteira = df_carteira.groupby("Produto", as_index=False).agg({
    "Valor aplicado": "sum",
    "Saldo bruto": "sum",
    "Rentabilidade (%)": "mean",
    "Participação na carteira (%)": "sum"
})

# --- Renomear colunas para padronizar ---
df_carteira.rename(columns={
    "Participação na carteira (%)": "ParticipacaoAtual",
    "Valor aplicado": "ValorAplicado",
    "Saldo bruto": "SaldoBruto",
    "Rentabilidade (%)": "Rentabilidade"
}, inplace=True)

df_alocacao.rename(columns={"Ativo": "Produto", "PercentualIdeal": "ParticipacaoIdeal"}, inplace=True)

# --- Unir Carteira com Alocacao ---
df = pd.merge(df_carteira, df_alocacao, on="Produto", how="left")

# --- Calcular diferença e status ---
df["Diferenca"] = df["ParticipacaoIdeal"] - df["ParticipacaoAtual"]

def status_icon(diff):
    if pd.isna(diff):
        return "⚪"
    elif diff > 0:
        return "🔵"  # Comprar
    elif diff < 0:
        return "🔴"  # Reduzir
    else:
        return "🟢"  # Ideal

df["Status"] = df["Diferenca"].apply(status_icon)

# --- Puxar valor atual de cada ativo ---
valores_atuais = {}
for produto in df["Produto"]:
    try:
        ticker = produto.split(" - ")[0].strip()
        data = yf.Ticker(ticker)
        valor = data.history(period="1d")["Close"].iloc[-1]
        valores_atuais[produto] = valor
    except:
        valores_atuais[produto] = None

df["ValorAtual"] = df["Produto"].map(valores_atuais)

# --- Formatação ---
df["ValorAplicado"] = df["ValorAplicado"].apply(lambda x: f"R${x:,.2f}")
df["SaldoBruto"] = df["SaldoBruto"].apply(lambda x: f"R${x:,.2f}")
df["ParticipacaoAtual"] = df["ParticipacaoAtual"].apply(lambda x: f"{x:.2f}%")
df["ParticipacaoIdeal"] = df["ParticipacaoIdeal"].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
df["Diferenca"] = df["Diferenca"].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
df["ValorAtual"] = df["ValorAtual"].apply(lambda x: f"R${x:,.2f}" if pd.notna(x) else "N/A")

st.subheader("Carteira Atual vs Alocação Ideal")
st.dataframe(df[["Produto", "ValorAplicado", "SaldoBruto", "ParticipacaoAtual", "ParticipacaoIdeal", "Diferenca", "Status", "ValorAtual"]])

# --- Caixa de aporte ---
aporte = st.number_input(
    "Qual o valor do aporte?",
    min_value=0.0,
    value=0.0,
    step=1.0,
    format="%.2f"
)

if aporte > 0:
    # Filtrar ativos para comprar (status azul)
    df_comprar = df[df["Status"] == "🔵"].copy()
    df_comprar = df_comprar.sort_values("Diferenca", ascending=False)

    total_diferenca = df_comprar["Diferenca"].apply(lambda x: float(x.strip('%')) if pd.notna(x) else 0).sum()
    if total_diferenca > 0:
        df_comprar["Aporte Recomendado"] = df_comprar["Diferenca"].apply(lambda x: float(x.strip('%')) if pd.notna(x) else 0) / total_diferenca * aporte
        df_comprar["Aporte Recomendado"] = df_comprar["Aporte Recomendado"].apply(lambda x: f"R${x:,.2f}")
    else:
        df_comprar["Aporte Recomendado"] = "R$0,00"

    st.subheader("Recomendações de Aporte")
    st.dataframe(df_comprar[["Produto", "ValorAtual", "Aporte Recomendado"]])
