import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Gestão de Carteira", layout="wide")
st.title("Gestão de Carteira")

# URLs das planilhas CSV públicas
URL_CARTEIRA = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=0"
URL_ALOCACAO = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=1042665035"

# Carregar dados
try:
    df_carteira = pd.read_csv(URL_CARTEIRA)
    df_alocacao = pd.read_csv(URL_ALOCACAO)
except Exception as e:
    st.error("Erro ao carregar os dados da planilha. Verifique o link e permissões.")
    st.stop()

# Padronizar nomes de colunas removendo espaços extras
df_carteira.columns = df_carteira.columns.str.strip()
df_alocacao.columns = df_alocacao.columns.str.strip()

# Padronizar nomes de ativos para filtragem futura
df_carteira["Produto"] = df_carteira["Produto"].str.strip().str.upper()
df_alocacao["Ativo"] = df_alocacao["Ativo"].str.strip().str.upper()

# Limpar e converter a coluna "Valor aplicado"
df_carteira["Valor aplicado"] = (
    df_carteira["Valor aplicado"]
    .astype(str)
    .str.replace("R$", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.strip()
)
df_carteira["Valor aplicado"] = pd.to_numeric(df_carteira["Valor aplicado"], errors="coerce")

# Limpar e converter a coluna "Saldo bruto"
df_carteira["Saldo bruto"] = (
    df_carteira["Saldo bruto"]
    .astype(str)
    .str.replace("R$", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.strip()
)
df_carteira["Saldo bruto"] = pd.to_numeric(df_carteira["Saldo bruto"], errors="coerce")

# Converter outras colunas numéricas da Carteira
numericas = ["Rentabilidade (%)", "Participação na carteira (%)"]
for col in numericas:
    df_carteira[col] = pd.to_numeric(
        df_carteira[col].astype(str).str.replace(",", ".").str.strip(),
        errors="coerce"
    )

# Limpar e converter a coluna "PercentualIdeal" da Alocacao
df_alocacao["PercentualIdeal"] = (
    df_alocacao["PercentualIdeal"]
    .astype(str)
    .str.replace("%", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.strip()
)
df_alocacao["PercentualIdeal"] = pd.to_numeric(df_alocacao["PercentualIdeal"], errors="coerce")

# Renomear coluna para padronização
df_alocacao.rename(columns={"PercentualIdeal": "ParticipacaoIdeal", "Ativo": "Produto"}, inplace=True)

# Agrupar Carteira por Produto, mantendo Valor Aplicado e Saldo Bruto originais
df_carteira = df_carteira.groupby("Produto", as_index=False).agg({
    "Valor aplicado": "first",
    "Saldo bruto": "first",
    "Rentabilidade (%)": "mean",
    "Participação na carteira (%)": "sum"
})

# Renomear colunas da Carteira
df_carteira.rename(columns={
    "Valor aplicado": "ValorAplicado",
    "Saldo bruto": "SaldoBruto",
    "Rentabilidade (%)": "Rentabilidade",
    "Participação na carteira (%)": "ParticipacaoAtual"
}, inplace=True)

# Merge Carteira + Alocacao
df = pd.merge(df_carteira, df_alocacao, on="Produto", how="left")

# FILTRO DEFINITIVO: ativos que não devem aparecer
ativos_excluir = ["BRCR11", "BTHF11", "RBFF11", "RBRD11", "RECR11", "TAEE4"]
df = df[~df["Produto"].isin(ativos_excluir)]

# Calcular diferença
df["Diferenca"] = df["ParticipacaoIdeal"] - df["ParticipacaoAtual"]

# Status com bolinhas coloridas
def status(row):
    if pd.isna(row["Diferenca"]):
        return "—"
    elif row["Diferenca"] > 0:
        return "🟢 Comprar mais"
    elif row["Diferenca"] < 0:
        return "🔴 Reduzir"
    else:
        return "🔵 Ok"

df["Status"] = df.apply(status, axis=1)

# Criar coluna Ticker para yfinance (ativos brasileiros terminam com .SA)
df["TickerYF"] = df["Produto"].apply(lambda x: f"{x}.SA" if not x.endswith(".SA") else x)

# Função para buscar valor atual
def get_valor_atual(ticker):
    try:
        ticker_data = yf.Ticker(ticker)
        price = ticker_data.history(period="1d")["Close"][-1]
        return price
    except:
        return None

# Aplicar a função
df["ValorAtual"] = df["TickerYF"].apply(get_valor_atual)

# Formatar valores monetários
df["ValorAplicado"] = df["ValorAplicado"].fillna(0).map(lambda x: f"R${x:,.2f}")
df["SaldoBruto"] = df["SaldoBruto"].fillna(0).map(lambda x: f"R${x:,.2f}")
df["ValorAtual"] = df["ValorAtual"].map(lambda x: f"R${x:,.2f}" if pd.notna(x) else "N/A")

# Formatar Participações como porcentagem
df["ParticipacaoAtual"] = df["ParticipacaoAtual"].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
df["ParticipacaoIdeal"] = df["ParticipacaoIdeal"].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")

# Exibir tabela principal
st.subheader("Carteira Atual vs Alocação Ideal")
df_exibir = df.rename(columns={
    "ValorAplicado": "Valor Aplicado",
    "SaldoBruto": "Saldo Bruto",
    "ParticipacaoAtual": "Participação Atual",
    "ParticipacaoIdeal": "Participação Ideal"
})

st.dataframe(df_exibir[["Produto", "Valor Aplicado", "Saldo Bruto",
                        "Participação Atual", "Participação Ideal",
                        "Diferenca", "Status", "ValorAtual"]])

# Caixa de entrada para aporte
aporte_str = st.text_input("Qual o valor do aporte?", "0.00")
try:
    aporte = float(aporte_str.replace(",", "."))
except ValueError:
    aporte = 0.0

if aporte > 0:
    df_comprar = df[df["Status"].str.contains("Comprar mais")].copy()
    total_diff = df_comprar["Diferenca"].sum()
    if total_diff > 0:
        df_comprar["Aporte Recomendado"] = (df_comprar["Diferenca"] / total_diff) * aporte
    else:
        df_comprar["Aporte Recomendado"] = 0

    df_comprar["Aporte Recomendado"] = df_comprar["Aporte Recomendado"].map("R${:,.2f}".format)
    df_comprar.sort_values("Diferenca", ascending=False, inplace=True)

    st.subheader("Recomendações de Aporte")
    st.dataframe(df_comprar[["Produto", "ValorAtual", "Aporte Recomendado", "Diferenca"]])
