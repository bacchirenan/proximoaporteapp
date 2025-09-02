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

# Padronizar colunas
df_carteira.columns = df_carteira.columns.str.strip()
df_alocacao.columns = df_alocacao.columns.str.strip()

# Extrair apenas o ticker (parte antes do "-") e padronizar
df_carteira["Produto"] = df_carteira["Produto"].str.split("-").str[0].str.strip().str.upper()
df_alocacao["Ativo"] = df_alocacao["Ativo"].str.split("-").str[0].str.strip().str.upper()

# Converter colunas monetárias
for col in ["Valor aplicado", "Saldo bruto"]:
    df_carteira[col] = (
        df_carteira[col].astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    df_carteira[col] = pd.to_numeric(df_carteira[col], errors="coerce")

# Converter outras colunas numéricas
for col in ["Rentabilidade (%)", "Participação na carteira (%)"]:
    df_carteira[col] = pd.to_numeric(df_carteira[col].astype(str).str.replace(",", "."), errors="coerce")

# Converter coluna PercentualIdeal
df_alocacao["PercentualIdeal"] = pd.to_numeric(
    df_alocacao["PercentualIdeal"].astype(str).str.replace(",", "."), errors="coerce"
)

# Renomear colunas
df_alocacao.rename(columns={"PercentualIdeal": "ParticipacaoIdeal", "Ativo": "Produto"}, inplace=True)

# Agrupar Carteira por Produto
df_carteira = df_carteira.groupby("Produto", as_index=False).agg({
    "Valor aplicado": "first",
    "Saldo bruto": "first",
    "Rentabilidade (%)": "mean",
    "Participação na carteira (%)": "sum"
})

df_carteira.rename(columns={
    "Valor aplicado": "ValorAplicado",
    "Saldo bruto": "SaldoBruto",
    "Rentabilidade (%)": "Rentabilidade",
    "Participação na carteira (%)": "ParticipacaoAtual"
}, inplace=True)

# Merge Carteira + Alocacao
df = pd.merge(df_carteira, df_alocacao, on="Produto", how="left")

# FILTRO DEFINITIVO
ativos_excluir = ["BRCR11", "BTHF11", "RBFF11", "RBRD11", "RECR11", "TAEE4"]
df = df[~df["Produto"].isin(ativos_excluir)]

# Calcular diferença
df["Diferenca"] = df["ParticipacaoIdeal"] - df["ParticipacaoAtual"]

# Status com bolinhas
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

# Mapeamento completo de tickers para yfinance
ticker_map = {
    "AAPL": "AAPL",
    "BBDC3": "BBDC3.SA",
    "BBSE3": "BBSE3.SA",
    "BTLG11": "BTLG11.SA",
    "CPLE6": "CPLE6.SA",
    "CRWD": "CRWD",
    "CSMG3": "CSMG3.SA",
    "DDOG": "DDOG",
    "DHS": "DHS",
    "GGBR4": "GGBR4.SA",
    "HSML11": "HSML11.SA",
    "IBIT": "IBIT",
    "IRDM11": "IRDM11.SA",
    "ITUB4": "ITUB4.SA",
    "KLBN4": "KLBN4.SA",
    "KNCR11": "KNCR11.SA",
    "KO": "KO",
    "MSFT": "MSFT",
    "MXRF11": "MXRF11.SA",
    "O": "O",
    "PVBI11": "PVBI11.SA",
    "RBRF11": "RBRF11.SA",
    "SAPR4": "SAPR4.SA",
    "SLCE3": "SLCE3.SA",
    "SNAG11": "SNAG11.SA",
    "SOXX": "SOXX",
    "TAEE11": "TAEE11.SA",
    "VILG11": "VILG11.SA",
    "VNQ": "VNQ",
    "VOO": "VOO",
    "WEGE3": "WEGE3.SA",
    "XOM": "XOM",
    "XPLG11": "XPLG11.SA",
    "XPML11": "XPML11.SA"
}

df["TickerYF"] = df["Produto"].map(ticker_map)

# Função para buscar valor atual atualizado
def get_valor_atual(ticker):
    if pd.isna(ticker):
        return None
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period="5d")
        if not hist.empty:
            return hist["Close"].iloc[-1]
        else:
            return ticker_obj.fast_info.get("last_price", None)
    except Exception as e:
        print(f"[ERRO] {ticker}: {e}")
        return None

# Aplicar ValorAtual
df["ValorAtual"] = df["TickerYF"].apply(get_valor_atual)
df["ValorAtual"] = df["ValorAtual"].map(lambda x: f"R${x:,.2f}" if pd.notna(x) else "N/A")

# Formatar valores e participações
df["ValorAplicado"] = df["ValorAplicado"].fillna(0).map(lambda x: f"R${x:,.2f}")
df["SaldoBruto"] = df["SaldoBruto"].fillna(0).map(lambda x: f"R${x:,.2f}")
df["ParticipacaoAtual"] = df["ParticipacaoAtual"].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
df["ParticipacaoIdeal"] = df["ParticipacaoIdeal"].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")

# Exibir tabelas iniciais
df_exibir = df.rename(columns={
    "ValorAplicado": "Valor Aplicado",
    "SaldoBruto": "Saldo Bruto",
    "ParticipacaoAtual": "Participação Atual",
    "ParticipacaoIdeal": "Participação Ideal"
})

# --- Ações nacionais ---
df_acoes = df_exibir[df_exibir["TickerYF"].str.endswith(".SA", na=False)]
df_acoes = df_acoes[~df_acoes["Produto"].str.endswith("11")]
st.subheader("Carteira Atual vs Alocação Ideal – Ações Nacionais")
st.table(df_acoes[["Produto", "Valor Aplicado", "Saldo Bruto",
                   "Participação Atual", "Participação Ideal",
                   "Diferenca", "Status", "ValorAtual"]].rename(columns={"ValorAtual": "Valor Atual"}))

# --- Fundos imobiliários ---
df_fiis = df_exibir[df_exibir["Produto"].str.endswith("11")]
st.subheader("Carteira Atual vs Alocação Ideal – Fundos Imobiliários")
st.table(df_fiis[["Produto", "Valor Aplicado", "Saldo Bruto",
                  "Participação Atual", "Participação Ideal",
                  "Diferenca", "Status", "ValorAtual"]].rename(columns={"ValorAtual": "Valor Atual"}))

# --- Ativos americanos ---
df_usa = df_exibir[~df_exibir["TickerYF"].str.endswith(".SA", na=False)]
st.subheader("Carteira Atual vs Alocação Ideal – Ativos Americanos")
st.table(df_usa[["Produto", "Valor Aplicado", "Saldo Bruto",
                 "Participação Atual", "Participação Ideal",
                 "Diferenca", "Status", "ValorAtual"]].rename(columns={"ValorAtual": "Valor Atual"}))

# Recomendação de aporte
aporte_str = st.text_input("Qual o valor do aporte?", "0.00")
processar = st.button("Processar aporte")

if processar:
    try:
        aporte = float(aporte_str.replace(",", "."))
    except ValueError:
        aporte = 0.0

    df_comprar = df[df["Status"].str.contains("Comprar mais")].copy()

    if not df_comprar.empty:
        # Ordenar pelo diferencial de alocação
        df_comprar = df_comprar.sort_values(by="Diferenca", ascending=False)

        # Aporte proporcional
        if aporte > 0:
            total_diff = df_comprar["Diferenca"].sum()
            if total_diff > 0:
                df_comprar["Aporte Recomendado"] = (df_comprar["Diferenca"] / total_diff) * aporte
            else:
                df_comprar["Aporte Recomendado"] = 0

            df_comprar["Aporte Recomendado"] = df_comprar["Aporte Recomendado"].map("R${:,.2f}".format)

        # Dividir recomendações por tipo de ativo
        df_rec_acoes = df_comprar[df_comprar["TickerYF"].str.endswith(".SA", na=False) & ~df_comprar["Produto"].str.endswith("11")]
        df_rec_fiis = df_comprar[df_comprar["Produto"].str.endswith("11")]
        df_rec_usa = df_comprar[~df_comprar["TickerYF"].str.endswith(".SA", na=False)]

        st.subheader("Recomendações de Aporte – Ações Nacionais")
        st.table(df_rec_acoes[["Produto", "ValorAtual", "Aporte Recomendado", "Diferenca"]].rename(columns={"ValorAtual": "Valor Atual"}))

        st.subheader("Recomendações de Aporte – Fundos Imobiliários")
        st.table(df_rec_fiis[["Produto", "ValorAtual", "Aporte Recomendado", "Diferenca"]].rename(columns={"ValorAtual": "Valor Atual"}))

        st.subheader("Recomendações de Aporte – Ativos Americanos")
        st.table(df_rec_usa[["Produto", "ValorAtual", "Aporte Recomendado", "Diferenca"]].rename(columns={"ValorAtual": "Valor Atual"}))
