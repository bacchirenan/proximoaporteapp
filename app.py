import streamlit as st
import pandas as pd
import yfinance as yf

# ------------------------------
# URLs das planilhas (CSV público)
# ------------------------------
URL_CARTEIRA = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=0"
URL_ALOCACAO = "https://docs.google.com/spreadsheets/d/1CXeUHvD-FG3uvkWSDnMKlFmmZAtMac9pzP8lhxNie74/export?format=csv&gid=1042665035"

# ------------------------------
# Função para formatar valores em R$
# ------------------------------
def formatar_real(valor):
    if pd.isna(valor):
        return "R$0,00"
    return "R${:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")

# ------------------------------
# Ler planilhas
# ------------------------------
df_carteira = pd.read_csv(URL_CARTEIRA)
df_alocacao = pd.read_csv(URL_ALOCACAO)

# ------------------------------
# Normalizar nomes das colunas
# ------------------------------
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

# ------------------------------
# Agrupar ativos repetidos
# ------------------------------
df_carteira = df_carteira.groupby("Ativo", as_index=False).agg({
    "Data da primeira aplicação": "min",
    "ValorAplicado": "sum",
    "SaldoBruto": "sum",
    "Rentabilidade": "mean",
    "ParticipacaoAtual": "sum"
})

# ------------------------------
# Merge Carteira x Alocacao
# ------------------------------
df = pd.merge(df_carteira, df_alocacao, on="Ativo", how="left")

# ------------------------------
# Cálculo de diferença e status
# ------------------------------
# Converter ParticipacaoAtual e Ideal para float
df["ParticipacaoAtual"] = pd.to_numeric(df["ParticipacaoAtual"], errors="coerce")
df["ParticipacaoIdeal"] = pd.to_numeric(df["ParticipacaoIdeal"], errors="coerce")
df["Diferenca"] = df["ParticipacaoIdeal"] - df["ParticipacaoAtual"]

def status_ativo(dif):
    if pd.isna(dif):
        return "Indefinido"
    elif dif > 0.01:
        return "🔵 Comprar mais"
    elif dif < -0.01:
        return "🔴 Reduzir"
    else:
        return "✅ Ideal"

df["Status"] = df["Diferenca"].apply(status_ativo)

# ------------------------------
# Puxar valor atual via yfinance
# ------------------------------
def pegar_valor_atual(ticker):
    try:
        symbol = ticker.split(" ")[0]  # pegar só o ticker
        valor = yf.Ticker(symbol).history(period="1d")["Close"].iloc[-1]
        return valor
    except:
        return None

df["ValorAtual"] = df["Ativo"].apply(pegar_valor_atual)

# ------------------------------
# Formatar valores monetários
# ------------------------------
for col in ["ValorAplicado", "SaldoBruto", "ParticipacaoAtual", "ParticipacaoIdeal", "Diferenca", "ValorAtual"]:
    df[col] = df[col].apply(formatar_real)

# ------------------------------
# Mostrar tabela principal
# ------------------------------
st.title("📊 Carteira vs Alocação Ideal")
st.dataframe(df[["Ativo","ValorAplicado","SaldoBruto","ParticipacaoAtual","ParticipacaoIdeal","Diferenca","Status","ValorAtual"]], use_container_width=True)

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
    # Só ativos que estão em 🔵 Comprar mais
    df_comprar = df[df["Status"] == "🔵 Comprar mais"].copy()
    
    if not df_comprar.empty:
        # Criar coluna numérica da diferença para cálculo
        df_comprar["Diferenca_num"] = df_comprar["Diferenca"].str.replace("R$", "").str.replace(".", "").str.replace(",", ".").astype(float)
        # Ordenar do mais descontado
        df_comprar = df_comprar.sort_values(by="Diferenca_num", ascending=False)
        
        # Calcular aporte proporcional
        df_comprar["Aporte Recomendado"] = df_comprar["Diferenca_num"] / df_comprar["Diferenca_num"].sum() * aporte
        df_comprar["Aporte Recomendado"] = df_comprar["Aporte Recomendado"].apply(formatar_real)
        
        df_recomendacao = df_comprar[["Ativo","ValorAtual","Aporte Recomendado"]]
        st.write("💡 Recomendação de aporte proporcional aos ativos mais descontados (🔵 Comprar mais):")
        st.dataframe(df_recomendacao, use_container_width=True)
    else:
        st.write("Todos os ativos estão na alocação ideal. Nenhum aporte necessário.")
else:
    st.write("Informe o valor do aporte para calcular a recomendação.")
