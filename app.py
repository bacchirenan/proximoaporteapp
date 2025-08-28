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

# Limpar e converter a coluna "Valor aplicado" corretamente
df_carteira["Valor aplicado"] = (
    df_carteira["Valor aplicado"]
    .astype(str)  # garante string
    .str.replace("R$", "", regex=False)  # remove R$
    .str.replace(".", "", regex=False)   # remove pontos de milhar
    .str.replace(",", ".", regex=False)  # transforma vírgula em ponto
    .str.strip()  # remove espaços
)
df_carteira["Valor aplicado"] = pd.to_numeric(df_carteira["Valor aplicado"], errors="coerce")

# Substituir vírgula por ponto e converter outras colunas numéricas
numericas = ["Saldo bruto", "Rentabilidade (%)", "Participação na carteira (%)"]
for col in numericas:
    df_carteira[col] = pd.to_numeric(
        df_carteira[col].astype(str).str.replace(",", ".").str.strip(),
        errors="coerce"
    )

df_alocacao["PercentualIdeal"] = pd.to_numeric(
    df_alocacao["PercentualIdeal"].astype(str).str.replace(",", ".").str.strip(),
    errors="coerce"
)

# Agrupar Carteira por Produto, mas manter Valor Aplicado original
df_carteira = df_carteira.groupby("Produto", as_index=False).agg({
    "Valor aplicado": "first",  # pega valor limpo da planilha
    "Saldo bruto": "sum",
    "Rentabilidade (%)": "mean",
    "Participação na carteira (%)": "sum"
})

# Renomear colunas para padronizar
df_carteira.rename(columns={
    "Valor aplicado": "ValorAplicado",
    "Saldo bruto": "SaldoBruto",
    "Rentabilidade (%)": "Rentabilidade",
    "Participação na carteira (%)": "ParticipacaoAtual"
}, inplace=True)
df_alocacao.rename(columns={"PercentualIdeal": "ParticipacaoIdeal", "Ativo": "Produto"}, inplace=True)

# Merge Carteira + Alocacao
df = pd.merge(df_carteira, df_alocacao, on="Produto", how="left")

# Calcular diferença e status
df["Diferenca"] = df["ParticipacaoIdeal"] - df["ParticipacaoAtual"]

def status(row):
    if pd.isna(row["Diferenca"]):
        return "—"
    elif row["Diferenca"] > 0:
        return "Comprar mais"
    elif row["Diferenca"] < 0:
        return "Reduzir"
    else:
        return "Ok"

df["Status"] = df.apply(status, axis=1)

# Buscar valor atual online
def get_valor_atual(ticker):
    try:
        ticker_data = yf.Ticker(ticker.split(" - ")[0])
        price = ticker_data.history(period="1d")["Close"][-1]
        return price
    except:
        return None

df["ValorAtual"] = df["Produto"].apply(get_valor_atual)

# Substituir NaN por 0 e formatar valores monetários
df["ValorAplicado"] = df["ValorAplicado"].fillna(0).map(lambda x: f"R${x:,.2f}")
df["SaldoBruto"] = df["SaldoBruto"].fillna(0).map(lambda x: f"R${x:,.2f}")
df["ValorAtual"] = df["ValorAtual"].fillna(0).map(lambda x: f"R${x:,.2f}")

# Formatar Participações como porcentagem
df["ParticipacaoAtual"] = df["ParticipacaoAtual"].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
df["ParticipacaoIdeal"] = df["ParticipacaoIdeal"].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")

# Exibir tabela principal
st.subheader("Carteira Atual vs Alocação Ideal")

# Renomear colunas para exibição final, incluindo Valor Aplicado com espaço
df_exibir = df.rename(columns={
    "ValorAplicado": "Valor Aplicado",
    "ParticipacaoAtual": "Participação Atual",
    "ParticipacaoIdeal": "Participação Ideal"
})

st.dataframe(df_exibir[["Produto", "Valor Aplicado", "SaldoBruto", 
                        "Participação Atual", "Participação Ideal", 
                        "Diferenca", "Status", "ValorAtual"]])

# Caixa de entrada para aporte
aporte_str = st.text_input("Qual o valor do aporte?", "0.00")
try:
    aporte = float(aporte_str.replace(",", "."))
except ValueError:
    aporte = 0.0

if aporte > 0:
    # Considerar apenas ativos para comprar mais
    df_comprar = df[df["Status"] == "Comprar mais"].copy()
    total_diff = df_comprar["Diferenca"].sum()
    if total_diff > 0:
        df_comprar["Aporte Recomendado"] = (df_comprar["Diferenca"] / total_diff) * aporte
    else:
        df_comprar["Aporte Recomendado"] = 0

    # Formatar valores
    df_comprar["Aporte Recomendado"] = df_comprar["Aporte Recomendado"].map("R${:,.2f}".format)

    # Ordenar do mais descontado para o menos
    df_comprar.sort_values("Diferenca", ascending=False, inplace=True)

    st.subheader("Recomendações de Aporte")
    st.dataframe(df_comprar[["Produto", "ValorAtual", "Aporte Recomendado", "Diferenca"]])
