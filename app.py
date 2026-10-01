"""
========================================================================================
DASHBOARD EXECUTIVO DE FATURAMENTO & INTELIGÊNCIA COMERCIAL
Autora: Caroline Rocha
Stack: Streamlit + DuckDB + Plotly + Parquet
========================================================================================
"""
# rodar writefile dentro do colab pra gerar o arquivo app.py
# %%writefile app.py


# Aqui vai o código da sua aplicação que preparamos
st.title("Painel de Faturamento")
# ...


import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuração da página
st.set_page_config(
    page_title="Inteligência Comercial | Faturamento",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS limpa e moderna
st.markdown("""
<style>
    .main-metric-card {
        background-color: #1E222B;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #2E3440;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #38BDF8;
    }
    .metric-label {
        font-size: 14px;
        color: #94A3B8;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# FUNÇÕES DE CARREGAMENTO COM CACHE (ALTA PERFORMANCE)
# --------------------------------------------------------------------------------------
@st.cache_resource
def get_db_connection():
    # Cria uma conexão em memória com o DuckDB
    con = duckdb.connect(database=':memory:')
    arquivo_parquet = "faturamento.parquet"
    if not os.path.exists(arquivo_parquet):
        # Fallback para caminho absoluto se rodando em pasta específica
        arquivo_parquet = "/mnt/documents/faturamento.parquet"
    con.execute(f"CREATE TABLE faturamento AS SELECT * FROM read_parquet('{arquivo_parquet}')")
    return con

con = get_db_connection()

# --------------------------------------------------------------------------------------
# BARRA LATERAL: FILTROS INTERATIVOS
# --------------------------------------------------------------------------------------
st.sidebar.title("🔍 Filtros de Análise")
st.sidebar.markdown("---")

# Filtro de Ano
anos_disponiveis = con.execute("SELECT DISTINCT ANO FROM faturamento ORDER BY ANO").df()['ANO'].tolist()
ano_selecionado = st.sidebar.multiselect("Ano de Referência", anos_disponiveis, default=anos_disponiveis)

# Filtro de Categoria
categorias_disponiveis = con.execute("SELECT DISTINCT Categoria FROM faturamento ORDER BY Categoria").df()['Categoria'].tolist()
categoria_selecionada = st.sidebar.multiselect("Categoria de Serviço", categorias_disponiveis, default=categorias_disponiveis)

# Filtro de Franqueado
franqueados_disponiveis = con.execute("SELECT DISTINCT Vendedor FROM faturamento ORDER BY Vendedor").df()['Vendedor'].tolist()
franqueado_selecionado = st.sidebar.multiselect("Franqueado / Vendedor", franqueados_disponiveis, default=[])

# Montagem dinâmica do WHERE em SQL
where_clauses = []
if ano_selecionado:
    where_clauses.append(f"ANO IN ({','.join(map(str, ano_selecionado))})")
if categoria_selecionada:
    cats_str = "', '".join([c.replace("'", "''") for c in categoria_selecionada])
    where_clauses.append(f"Categoria IN ('{cats_str}')")
if franqueado_selecionado:
    franq_str = "', '".join([f.replace("'", "''") for f in franqueado_selecionado])
    where_clauses.append(f"Vendedor IN ('{franq_str}')")

where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

# --------------------------------------------------------------------------------------
# CABEÇALHO DO DASHBOARD
# --------------------------------------------------------------------------------------
st.title("📊 Painel Executivo de Faturamento e Concentração")
st.markdown("Análise comercial automatizada com **DuckDB** e **Plotly** baseada em dados ERP transacionais.")

# --------------------------------------------------------------------------------------
# CARTÕES DE KPI (BIG NUMBERS)
# --------------------------------------------------------------------------------------
query_kpi = f"""
SELECT 
    COUNT(*) as total_faturas,
    COALESCE(SUM(ValorTotalServico), 0) as receita_bruta,
    COALESCE(SUM(ValorLiquido), 0) as receita_liquida,
    COALESCE(AVG(ValorTotalServico), 0) as ticket_medio,
    COUNT(DISTINCT Cliente) as clientes_unicos,
    COUNT(DISTINCT Vendedor) as franqueados_ativos
FROM faturamento
{where_sql}
"""
kpi_data = con.execute(query_kpi).df().iloc[0]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Faturamento Bruto",
        value=f"R$ {kpi_data['receita_bruta']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
with col2:
    st.metric(
        label="Faturamento Líquido",
        value=f"R$ {kpi_data['receita_liquida']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
with col3:
    st.metric(
        label="Ticket Médio / Fatura",
        value=f"R$ {kpi_data['ticket_medio']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
with col4:
    st.metric(
        label="Faturas Emitidas",
        value=f"{int(kpi_data['total_faturas']):,}".replace(",", ".")
    )

st.markdown("---")

# --------------------------------------------------------------------------------------
# ABAS DE NAVEGAÇÃO
# --------------------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📈 Evolução & Sazonalidade",
    "🎯 Curva ABC / Risco (Pareto)",
    "🏢 Franqueados & Carteira"
])

# --------------------------------------------------------------------------------------
# ABA 1: EVOLUÇÃO TEMPORAL
# --------------------------------------------------------------------------------------
with tab1:
    st.subheader("Evolução Histórica do Faturamento")
    
    query_mes = f"""
    SELECT 
        AnoMes,
        ANO,
        MES,
        ROUND(SUM(ValorTotalServico), 2) as Faturamento,
        COUNT(*) as Faturas
    FROM faturamento
    {where_sql}
    GROUP BY AnoMes, ANO, MES
    ORDER BY AnoMes
    """
    df_mes = con.execute(query_mes).df()
    
    if not df_mes.empty:
        # Gráfico interativo com Plotly
        fig_evolucao = px.line(
            df_mes,
            x="AnoMes",
            y="Faturamento",
            markers=True,
            title="Receita Mensal (R$)",
            color_discrete_sequence=["#38BDF8"],
            labels={"AnoMes": "Mês/Ano", "Faturamento": "Faturamento (R$)"}
        )
        fig_evolucao.update_layout(template="plotly_dark", height=420)
        st.plotly_chart(fig_evolucao, use_container_width=True)
        
        # Comparativo por Ano
        query_ano = f"""
        SELECT 
            ANO,
            ROUND(SUM(ValorTotalServico), 2) as Faturamento,
            COUNT(*) as Qtd_Faturas,
            ROUND(AVG(ValorTotalServico), 2) as Ticket_Medio
        FROM faturamento
        {where_sql}
        GROUP BY ANO
        ORDER BY ANO
        """
        df_ano = con.execute(query_ano).df()
        
        fig_bar_ano = px.bar(
            df_ano,
            x="ANO",
            y="Faturamento",
            text="Faturamento",
            title="Comparativo Anual Consolidado",
            color_discrete_sequence=["#6366F1"]
        )
        fig_bar_ano.update_traces(texttemplate='R$ %{text:,.2s}', textposition='outside')
        fig_bar_ano.update_layout(template="plotly_dark", height=380)
        st.plotly_chart(fig_bar_ano, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

# --------------------------------------------------------------------------------------
# ABA 2: CURVA ABC / PARETO 80/20
# --------------------------------------------------------------------------------------
with tab2:
    st.subheader("Curva ABC de Clientes (Concentração de Receita)")
    st.markdown("""
    A análise de Pareto identifica o grau de dependência da empresa em relação a poucos grandes clientes:
    * **Classe A:** Clientes que compõem os primeiros **80% da receita**.
    * **Classe B:** Clientes nos **15% seguintes**.
    * **Classe C:** Clientes da 'cauda longa' (**5% restantes**).
    """)
    
    query_pareto_app = f"""
    WITH fat_cli AS (
        SELECT 
            Cliente,
            COUNT(*) as Compras,
            ROUND(SUM(ValorTotalServico), 2) as Faturamento
        FROM faturamento
        {where_sql}
        GROUP BY Cliente
    ),
    acum AS (
        SELECT 
            Cliente,
            Compras,
            Faturamento,
            SUM(Faturamento) OVER (ORDER BY Faturamento DESC) as S_Acum,
            SUM(Faturamento) OVER () as S_Total
        FROM fat_cli
    )
    SELECT 
        Cliente,
        Compras,
        Faturamento,
        ROUND((S_Acum / S_Total) * 100, 2) as Pct_Acumulado,
        CASE 
            WHEN (S_Acum / S_Total) <= 0.80 THEN 'Classe A (80%)'
            WHEN (S_Acum / S_Total) <= 0.95 THEN 'Classe B (15%)'
            ELSE 'Classe C (5%)'
        END as Classe
    FROM acum
    ORDER BY Faturamento DESC
    """
    df_pareto_app = con.execute(query_pareto_app).df()
    
    if not df_pareto_app.empty:
        # Gráfico de pizza / distribuição das classes
        dist_classe = df_pareto_app.groupby("Classe")["Faturamento"].sum().reset_index()
        fig_pie = px.pie(
            dist_classe,
            names="Classe",
            values="Faturamento",
            title="Distribuição do Faturamento por Classe ABC",
            color="Classe",
            color_discrete_map={
                'Classe A (80%)': '#10B981',
                'Classe B (15%)': '#F59E0B',
                'Classe C (5%)': '#EF4444'
            }
        )
        fig_pie.update_layout(template="plotly_dark", height=380)
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Tabela dos Maiores Clientes
        st.markdown("#### Top 15 Maiores Clientes")
        st.dataframe(
            df_pareto_app.head(15).style.format({
                "Faturamento": "R$ {:,.2f}",
                "Pct_Acumulado": "{:.2f}%"
            }),
            use_container_width=True
        )

# --------------------------------------------------------------------------------------
# ABA 3: PERFORMANCE DE FRANQUEADOS
# --------------------------------------------------------------------------------------
with tab3:
    st.subheader("Performance Comercial por Franqueado / Vendedor")
    
    query_franq = f"""
    SELECT 
        Vendedor as Franqueado,
        COUNT(*) as Faturas,
        COUNT(DISTINCT Cliente) as Clientes_Atendidos,
        ROUND(SUM(ValorTotalServico), 2) as Faturamento_Total,
        ROUND(AVG(ValorTotalServico), 2) as Ticket_Medio
    FROM faturamento
    {where_sql}
    GROUP BY Vendedor
    ORDER BY Faturamento_Total DESC
    """
    df_franq = con.execute(query_franq).df()
    
    if not df_franq.empty:
        fig_franq = px.bar(
            df_franq.head(15),
            x="Franqueado",
            y="Faturamento_Total",
            text="Faturamento_Total",
            title="Top 15 Franqueados por Faturamento (R$)",
            color="Faturamento_Total",
            color_continuous_scale="Viridis"
        )
        fig_franq.update_traces(texttemplate='R$ %{text:,.2s}', textposition='outside')
        fig_franq.update_layout(template="plotly_dark", height=450)
        st.plotly_chart(fig_franq, use_container_width=True)
        
        st.dataframe(
            df_franq.style.format({
                "Faturamento_Total": "R$ {:,.2f}",
                "Ticket_Medio": "R$ {:,.2f}"
            }),
            use_container_width=True
        )

# Rodapé
st.markdown("---")
st.caption("Desenvolvido por Caroline Rocha | Análise de Dados com Python, DuckDB e Streamlit")
