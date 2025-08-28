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
# Função para limpar valores monetários
# ------------------------------
def parse_valor(valor):
    if pd.isna(valor):
        return 0
    valor = re.sub(r"[^\d,.-]", "", str(valor))  # Remove tudo que não seja número, vírgula ou ponto
    valor = valor.replace(",", ".")
    try:
        return float(valor)
    except:
        return 0

# Limpar colunas da carteira
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
# Limpar alocação
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

# ------------------------------
# Função para ícones
# ------------------------------
def icone_diferenca(x):
    if x > 0:
        return "🔵"  # Comprar mais
    elif x < 0:
        return "🔴"  # Reduzir
    else:
        return "✅"  # Ideal

df["Status"] = df["Diferenca"].apply(icone_diferenca)

# Mostrar tabela completa
df_display = df[["Produto", "ValorAplicado", "SaldoBruto", "ParticipacaoAtual", "ParticipacaoIdeal", "Diferenca", "Status"]]
st.title("📊 Carteira vs Alocação Ideal")
st.dataframe(df_display, use_container_width=True)

# ------------------------------
# Função para pegar preço atual via Yahoo Finance
# ------------------------------
@st.cache_data(ttl=600)
def preco_atual(ticker):
    try:
        ativo = yf.Ticker(ticker)
        preco = ativo.history(period="1d")["Close"].iloc[-1]
        return preco
    except:
        return None

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
    # Filtrar apenas ativos que precisam comprar mais (azuis)
    df_comprar = df[df["Diferenca"] > 0].copy()
    
    if not df_comprar.empty:
        # Ordenar do maior para o menor diferença
        df_comprar = df_comprar.sort_values(by="Diferenca", ascending=False)
        
        # Buscar preço atual de cada ativo
        df_comprar["ValorAtual"] = df_comprar["Produto"].apply(preco_atual)
        
        # Calcular total de diferenças
        total_diferenca = df_comprar["Diferenca"].sum()
        # Distribuir aporte proporcionalmente
        df_comprar["AporteRecomendado"] = df_comprar["Diferenca"] / total_diferenca * aporte
        
        # Criar a tabela final de recomendações
        df_recomendacao = df_comprar[["Produto", "ValorAtual", "Diferenca", "AporteRecomendado"]]
        
        st.write("💡 Recomendação de aporte proporcional aos ativos mais descontados (🔵 Comprar mais):")
        st.dataframe(df_recomendacao, use_container_width=True)
    else:
        st.write("Todos os ativos estão na alocação ideal. Nenhum aporte necessário.")
else:
    st.write("Informe o valor do aporte para calcular a recomendação.")
