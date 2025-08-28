import streamlit as st
import pandas as pd
import re
import yfinance as yf

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
# Limpeza de valores monetários
# ------------------------------
def parse_valor(valor):
    if pd.isna(valor):
        return 0
    valor = re.sub(r"[^\d,.-]", "", str(valor))
    valor = valor.replace(",", ".")
    try:
        return float(valor)
    except:
        return 0

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
# Alocação
# ------------------------------
df_alocacao = df_alocacao.rename(columns={"Ativo": "Produto", "PercentualIdeal": "ParticipacaoIdeal"})
df_alocacao["ParticipacaoIdeal"] = df_alocacao["ParticipacaoIdeal"].apply(parse_valor)

# Merge Carteira x Alocacao
df = pd.merge(df_carteira, df_alocacao, on="Produto", how="outer")
for col in ["ValorAplicado", "SaldoBruto", "ParticipacaoAtual", "ParticipacaoIdeal"]:
    df[col] = df[col].fillna(0)

df["Diferenca"] = df["ParticipacaoIdeal"] - df["ParticipacaoAtual"]

# ------------------------------
# Status de alocação
# ------------------------------
def icone_diferenca(x):
    if x > 0:
        return "🔵"  # Comprar mais
    elif x < 0:
        return "🔴"  # Reduzir
    else:
        return "✅"  # Ideal

df["Status"] = df["Diferenca"].apply(icone_diferenca)

# ------------------------------
# Mapear tickers manualmente
# ------------------------------
map_tickers = {
    # FIIs BR
    "MXRF11 - FII MAXI REN": "MXRF11.SA",
    "KNRI11 - FII KINEA": "KNRI11.SA",
    "KNCR11 - FII KINEA RI": "KNCR11.SA",
    "XPML11 - FII XP MALLS": "XPML11.SA",
    "SNAG11 - FIAGRO SUNO CI": "SNAG11.SA",
    "HSML11 - FII HSI MALL": "HSML11.SA",
    
    # Ações BR
    "TAEE11 - TAESA": "TAEE11.SA",
    "SAPR4 - SANEPAR": "SAPR4.SA",
    "CSMG3 - COPASA": "CSMG3.SA",
    "CPLE6 - COPEL": "CPLE6.SA",
    "BBSE3 - BBSEGURIDADE": "BBSE3.SA",
    "BBDC3 - BRADESCO": "BBDC3.SA",
    
    # Ações EUA / ETFs
    "AAPL - Apple Inc.": "AAPL",
    "MSFT - Microsoft Corporation": "MSFT",
    "VOO - Vanguard S&P 500 ETF": "VOO",
    "SOXX - iShares PHLX SOX Semiconductor Sector Index Fund": "SOXX",
    "DDOG - Datadog, Inc.": "DDOG",
    "CRWD - CrowdStrike Holdings, Inc.": "CRWD",
    "O - Realty Income Corporation": "O",
    "KO - Coca": "KO",
}

def obter_ticker(produto):
    return map_tickers.get(produto, None)

# ------------------------------
# Função para preço atual
# ------------------------------
@st.cache_data(ttl=600)
def preco_atual(ticker):
    if ticker is None:
        return None
    try:
        ativo = yf.Ticker(ticker)
        preco = ativo.history(period="1d")["Close"].iloc[-1]
        return round(preco, 2)
    except:
        return None

# Atualizar Valor Atual na tabela principal
df["Ticker"] = df["Produto"].apply(obter_ticker)
df["ValorAtual"] = df["Ticker"].apply(preco_atual)

# ------------------------------
# Tabela principal
# ------------------------------
df_display = df[["Produto", "ValorAplicado", "SaldoBruto", "ParticipacaoAtual", "ParticipacaoIdeal", "Diferenca", "Status", "ValorAtual"]]
st.title("📊 Carteira vs Alocação Ideal")
st.dataframe(df_display, use_container_width=True)

# ------------------------------
# Caixa de aporte
# ------------------------------
st.subheader("💰 Simulação de Aporte")
aporte_input = st.text_input("Qual o valor do aporte?", "0")

try:
    aporte = float(aporte_input.replace(",", "."))
except:
    st.error("Digite um valor numérico válido para o aporte.")
    aporte = 0

if aporte > 0:
    df_comprar = df[df["Diferenca"] > 0].copy()
    
    if not df_comprar.empty:
        df_comprar = df_comprar.sort_values(by="Diferenca", ascending=False)
        df_comprar["AporteRecomendado"] = df_comprar["Diferenca"] / df_comprar["Diferenca"].sum() * aporte
        
        df_recomendacao = df_comprar[["Produto", "ValorAtual", "Diferenca", "AporteRecomendado"]]
        st.write("💡 Recomendação de aporte proporcional aos ativos mais descontados (🔵 Comprar mais):")
        st.dataframe(df_recomendacao, use_container_width=True)
    else:
        st.write("Todos os ativos estão na alocação ideal. Nenhum aporte necessário.")
else:
    st.write("Informe o valor do aporte para calcular a recomendação.")
