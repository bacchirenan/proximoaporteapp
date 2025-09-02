# ==============================
# Recomendação de aporte
# ==============================
aporte_str = st.text_input("Qual o valor do aporte?", "0.00")
processar = st.button("Processar aporte")

if processar:
    try:
        aporte = float(aporte_str.replace(",", "."))
    except ValueError:
        aporte = 0.0

    df_comprar = df[df["Status"].str.contains("Comprar mais")].copy()
    
    if not df_comprar.empty:
        # Calcular Preço Médio Pago
        def preco_medio(row):
            try:
                valor_atual = float(str(row["ValorAtual"]).replace("R$", "").replace(",", "").replace("N/A", "0"))
                saldo_bruto = float(str(row["SaldoBruto"]).replace("R$", "").replace(",", ""))
                if valor_atual > 0:
                    qtde = saldo_bruto / valor_atual
                    return saldo_bruto / qtde
                else:
                    return 0
            except:
                return 0

        df_comprar["PrecoMedioPago"] = df_comprar.apply(preco_medio, axis=1)
        
        # Ordenar do mais barato para o mais caro
        df_comprar = df_comprar.sort_values(by="PrecoMedioPago", ascending=True)

        if aporte > 0:
            total_diff = df_comprar["Diferenca"].sum()
            if total_diff > 0:
                df_comprar["Aporte Recomendado"] = (df_comprar["Diferenca"] / total_diff) * aporte
            else:
                df_comprar["Aporte Recomendado"] = 0
            df_comprar["Aporte Recomendado"] = df_comprar["Aporte Recomendado"].map("R${:,.2f}".format)
        
        # Formatar Preço Médio Pago
        df_comprar["PrecoMedioPago"] = df_comprar["PrecoMedioPago"].map(lambda x: f"R${x:,.2f}")

    # Dividir recomendações por tipo de ativo
    df_rec_acoes = df_comprar[df_comprar["TickerYF"].str.endswith(".SA", na=False) & ~df_comprar["Produto"].str.endswith("11")]
    df_rec_fiis = df_comprar[df_comprar["Produto"].str.endswith("11")]
    df_rec_usa = df_comprar[~df_comprar["TickerYF"].str.endswith(".SA", na=False)]

    st.subheader("Recomendações de Aporte – Ações Nacionais")
    st.dataframe(df_rec_acoes[["Produto", "ValorAtual", "PrecoMedioPago", "Aporte Recomendado", "Diferenca", "Desconto (%)"]])

    st.subheader("Recomendações de Aporte – Fundos Imobiliários")
    st.dataframe(df_rec_fiis[["Produto", "ValorAtual", "PrecoMedioPago", "Aporte Recomendado", "Diferenca", "Desconto (%)"]])

    st.subheader("Recomendações de Aporte – Ativos Americanos")
    st.dataframe(df_rec_usa[["Produto", "ValorAtual", "PrecoMedioPago", "Aporte Recomendado", "Diferenca", "Desconto (%)"]])
