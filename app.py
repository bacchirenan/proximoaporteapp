import streamlit as st
import pandas as pd
import yfinance as yf

st.title("Gestão de Carteira")

# --- URLs das planilhas públicas (CSV export) ---
CARTEIRA_URL = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=0"
ALOCACAO_URL = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=1042665035"

# --- Ler CSVs ---
df_carteira = pd.read_csv(CARTEIRA_URL)
df_alocacao = pd.read_csv(ALOCACAO_URL)

# --- Renomear colunas para padrão interno ---
df_carteira.rename(columns={
    "Produto": "Ativo",
    "Valor aplicado": "ValorAplicado",
    "Saldo bruto": "SaldoBruto",
    "Participação na carteira (%)": "ParticipacaoAtual",
    "Rentabilidade (%)": "Rentabilidade"
}, inplace=True)

df_alocacao.rename(columns={
    "PercentualIdeal": "ParticipacaoIdeal"
}, inplace=True)

# --- Converter colunas numéricas ---
for col in ["ValorAplicado", "SaldoBruto", "Rentabilidade", "ParticipacaoAtual", "ParticipacaoIdeal"]:
    if col in df_carteira.columns:
        df_carteira[col] = pd.to_numeric(df_carteira[col], errors="coerce").fillna(0)
    if col in df_alocacao.columns:
        df_alocacao[col] = pd.to_numeric(df_alocacao[col], errors="coerce").fillna(0)

# --- Agrupar ativos repetidos na carteira ---
df_carteira = df_carteira.groupby("Ativo", as_index=False).agg({
    "Data da primeira aplicação": "min",
    "ValorAplicado": "sum",
    "SaldoBruto": "sum",
    "Rentabilidade": "mean",
    "ParticipacaoAtual": "sum"
})

# --- Merge com alocação ---
df = pd.merge(df_carteira, df_alocacao, on="Ativo", how="left")

# --- Calcular diferença ---
df["Diferenca"] = df["ParticipacaoIdeal"] - df["ParticipacaoAtual"]

# --- Status (verde = ideal, azul = comprar, vermelho = reduzir) ---
def status_color(x):
    if x == 0:
        return "🟢 Ideal"
    elif x > 0:
        return "🔵 Comprar"
    else:
        return "🔴 Reduzir"

df["Status"] = df["Diferenca"].apply(status_color)

# --- Buscar valor atual via yfinance ---
def get_valor_atual(ticker):
    try:
        data = yf.Ticker(ticker.split()[0])  # Pega só o ticker antes do "-"
        return data.history(period="1d")["Close"][-1]
    except:
        return None

df["ValorAtual"] = df["Ativo"].apply(get_valor_atual)

# --- Formatação monetária ---
for col in ["ValorAplicado", "SaldoBruto", "ValorAtual"]:
    df[col] = df[col].apply(lambda x: f"R${x:,.2f}" if pd.notnull(x) else "N/A")

# --- Mostrar tabela principal ---
st.subheader("Carteira Atual vs Alocação Ideal")
st.dataframe(df[["Ativo", "ValorAplicado", "SaldoBruto", "ParticipacaoAtual", "ParticipacaoIdeal", "Diferenca", "Status", "ValorAtual"]])

# --- Caixa de aporte ajustada para centavos ---
aporte = st.number_input(
    "Qual o valor do aporte?", 
    min_value=0.0, 
    step=0.01,       # passo mínimo em centavos
    format="%.2f"    # formatação para 2 casas decimais
)

if aporte > 0:
    # --- Filtrar ativos para comprar (status azul) ---
    df_comprar = df[df["Status"] == "🔵 Comprar"].copy()
    df_comprar = df_comprar.sort_values("Diferenca", ascending=False)

    # --- Calcular aporte recomendado proporcional à diferença ---
    total_diferenca = df_comprar["Diferenca"].sum()
    if total_diferenca > 0:
        df_comprar["Aporte Recomendado"] = df_comprar["Diferenca"] / total_diferenca * aporte
        df_comprar["Aporte Recomendado"] = df_comprar["Aporte Recomendado"].apply(lambda x: f"R${x:,.2f}")
    else:
        df_comprar["Aporte Recomendado"] = "R$0,00"

    st.subheader("Recomendações de Aporte")
    st.dataframe(df_comprar[["Ativo", "ValorAtual", "Aporte Recomendado"]])
