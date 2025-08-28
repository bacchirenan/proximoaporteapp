# ------------------------------
# Função para formatar valores em R$
# ------------------------------
def formatar_real(valor):
    if pd.isna(valor):
        return "R$0,00"
    return "R${:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")

# ------------------------------
# Tabela principal formatada
# ------------------------------
df_display = df[["Produto", "ValorAplicado", "SaldoBruto", "ParticipacaoAtual", "ParticipacaoIdeal", "Diferenca", "Status", "ValorAtual"]].copy()
for col in ["ValorAplicado", "SaldoBruto", "ParticipacaoAtual", "ParticipacaoIdeal", "Diferenca", "ValorAtual"]:
    df_display[col] = df_display[col].apply(formatar_real)

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
        df_comprar["Aporte Recomendado"] = df_comprar["Diferenca"] / df_comprar["Diferenca"].sum() * aporte
        
        # Formatar valores monetários
        for col in ["ValorAtual", "Aporte Recomendado"]:
            df_comprar[col] = df_comprar[col].apply(formatar_real)
        
        df_recomendacao = df_comprar[["Produto", "ValorAtual", "Diferenca", "Aporte Recomendado"]]
        st.write("💡 Recomendação de aporte proporcional aos ativos mais descontados (🔵 Comprar mais):")
        st.dataframe(df_recomendacao, use_container_width=True)
    else:
        st.write("Todos os ativos estão na alocação ideal. Nenhum aporte necessário.")
else:
    st.write("Informe o valor do aporte para calcular a recomendação.")
