import streamlit as st
import pandas as pd
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials

# ===== CONFIGURAÇÃO DA PÁGINA =====
st.set_page_config(page_title="Carteira Inteligente", page_icon="💰", layout="centered")

st.title("💰 Carteira Inteligente")
st.write("App para indicar em qual ativo aportar no momento, baseado na alocação ideal.")

# ======== CREDENCIAIS GOOGLE SHEETS ========
# Você vai precisar colocar as credenciais JSON da API do Google em um "secret" no Streamlit Cloud
# Exemplo: st.secrets["gcp_service_account"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
gc = gspread.authorize(credentials)

# ======== LEITURA DAS PLANILHAS ========
# Crie duas abas na mesma planilha:
# 1. "Carteira" -> colunas: Ativo, Quantidade
# 2. "Alocacao" -> colunas: Ativo, PercentualIdeal
SPREADSHEET_URL = st.secrets["spreadsheet_url"]  # coloque a URL da sua planilha no secrets
sh = gc.open_by_url(SPREADSHEET_URL)

df_carteira = pd.DataFrame(sh.worksheet("Carteira").get_all_records())
df_alocacao = pd.DataFrame(sh.worksheet("Alocacao").get_all_records())

# ======== INPUT DO USUÁRIO ========
aporte = st.number_input("Digite o valor do aporte (R$):", min_value=10.0, step=10.0)

if aporte:
    # ======== PEGAR PREÇOS ATUAIS ========
    tickers = list(df_carteira["Ativo"].unique())
    precos = {}
    for t in tickers:
        try:
            preco = yf.Ticker(t + ".SA").history(period="1d")["Close"].iloc[-1]  # B3
        except:
            preco = yf.Ticker(t).history(period="1d")["Close"].iloc[-1]  # USA
        precos[t] = preco

    # ======== CALCULAR VALORES ATUAIS ========
    df_carteira["PrecoAtual"] = df_carteira["Ativo"].map(precos)
    df_carteira["ValorAtual"] = df_carteira["Quantidade"] * df_carteira["PrecoAtual"]

    total_atual = df_carteira["ValorAtual"].sum()
    df_carteira["%Atual"] = df_carteira["ValorAtual"] / total_atual * 100

    # Juntar com a alocação ideal
    df = pd.merge(df_carteira, df_alocacao, on="Ativo", how="left")
    df["Defasagem"] = df["PercentualIdeal"] - df["%Atual"]

    # ======== PRIORIZAÇÃO ========
    # Ordena por maior defasagem (ativos abaixo da meta) e preço mais baixo
    df_prioridade = df.sort_values(by=["Defasagem", "PrecoAtual"], ascending=[False, True])

    # ======== SUGESTÃO DE COMPRA ========
    sugestoes = []
    valor_restante = aporte

    for _, row in df_prioridade.iterrows():
        if valor_restante <= 0:
            break
        preco = row["PrecoAtual"]
        max_cotas = int(valor_restante // preco)
        if max_cotas > 0:
            sugestoes.append({
                "Ativo": row["Ativo"],
                "QtdComprar": max_cotas,
                "ValorInvestido": max_cotas * preco,
                "PrecoAtual": preco,
                "Defasagem(%)": round(row["Defasagem"], 2)
            })
            valor_restante -= max_cotas * preco

    df_sugestoes = pd.DataFrame(sugestoes)

    st.subheader("📊 Sugestão de Aporte")
    st.dataframe(df_sugestoes)

    st.write(f"💵 Valor restante não alocado: R$ {valor_restante:.2f}")

    # Exportar CSV
    csv = df_sugestoes.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar sugestão em CSV", data=csv, file_name="sugestao_aporte.csv", mime="text/csv")
