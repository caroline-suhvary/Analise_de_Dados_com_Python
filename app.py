import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuração da página
st.set_page_config(
    page_title="Inteligência Comercial & Faturamento",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização visual limpa e elegante (compatível com tema claro e escuro)
st.markdown("""
<style>
    /* Cartões de métricas */
    div[data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.06);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        opacity: 0.8;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        font-weight: 700 !important;
    }
    /* Estilização de abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# FUNÇÕES UTILITÁRIAS DE FORMATAÇÃO (PADRÃO BRASILEIRO R$)
# --------------------------------------------------------------------------------------
def formata_brl(valor):
    """Converte número float em formato monetário brasileiro: R$ 1.234.567,89"""
    if pd.isna(valor) or valor is None:
        return "R$ 0,00"
    return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formata_inteiro(valor):
    """Converte inteiro em formato brasileiro: 1.234"""
    if pd.isna(valor) or valor is None:
        return "0"
    return f"{int(valor):,}".replace(",", ".")

def formata_percentual(valor):
    """Converte taxa em percentual brasileiro: 12,34%"""
    if pd.isna(valor) or valor is None:
        return "0,00%"
    return f"{float(valor):,.2f}%".replace(".", ",")

# --------------------------------------------------------------------------------------
# CARREGAMENTO DOS DADOS (DUCKDB)
# --------------------------------------------------------------------------------------
@st.cache_resource
def get_db_connection():
    con = duckdb.connect(database=':memory:')
    candidatos = [
        "FaturamentoEmpresaXYZ_ficticio_TUDO.csv",
        "faturamento_anonimizado.csv",
        "faturamento.parquet",
        "dados.csv"
    ]
    arquivo_escolhido = None
    for nome in candidatos:
        if os.path.exists(nome):
            arquivo_escolhido = nome
            break
        elif os.path.exists(os.path.join("/mnt/documents", nome)):
            arquivo_escolhido = os.path.join("/mnt/documents", nome)
            break
            
    if not arquivo_escolhido:
        raise FileNotFoundError("Nenhum arquivo de dados encontrado no repositório.")
        
    if arquivo_escolhido.endswith('.parquet'):
        con.execute(f"CREATE TABLE faturamento AS SELECT * FROM read_parquet('{arquivo_escolhido}')")
    else:
        con.execute(f"CREATE TABLE faturamento AS SELECT * FROM read_csv_auto('{arquivo_escolhido}')")
    return con

con = get_db_connection()

# --------------------------------------------------------------------------------------
# BARRA LATERAL: FILTROS
# --------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Painel de Filtros")
    st.caption("Refine os indicadores por período e segmento.")
    st.markdown("---")
    
    anos_disponiveis = con.execute("SELECT DISTINCT ANO FROM faturamento ORDER BY ANO").df()['ANO'].tolist()
    ano_selecionado = st.multiselect("Ano de Emissão", anos_disponiveis, default=anos_disponiveis)
    
    categorias_disponiveis = con.execute("SELECT DISTINCT Categoria FROM faturamento ORDER BY Categoria").df()['Categoria'].tolist()
    categoria_selecionada = st.multiselect("Categoria de Serviço", categorias_disponiveis, default=categorias_disponiveis)
    
    franqueados_disponiveis = con.execute("SELECT DISTINCT Vendedor FROM faturamento ORDER BY Vendedor").df()['Vendedor'].tolist()
    franqueado_selecionado = st.multiselect("Franqueado / Vendedor", franqueados_disponiveis, default=[])
    
    st.markdown("---")
    st.caption("💡 **Dica:** Deixar vazio em Franqueado considera toda a rede.")

# Montagem segura do WHERE
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
# CABEÇALHO PRINCIPAL
# --------------------------------------------------------------------------------------
st.title("📊 Faturamento & Performance Comercial")
st.markdown("Monitoramento executivo de receita, concentração de clientes e rede de franqueados.")
st.markdown("")

# --------------------------------------------------------------------------------------
# BIG NUMBERS (KPIs)
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

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(label="Faturamento Bruto Total", value=formata_brl(kpi_data['receita_bruta']))
with c2:
    st.metric(label="Faturamento Líquido", value=formata_brl(kpi_data['receita_liquida']))
with c3:
    st.metric(label="Ticket Médio por Nota", value=formata_brl(kpi_data['ticket_medio']))
with c4:
    st.metric(
        label="Volume Operacional",
        value=f"{formata_inteiro(kpi_data['total_faturas'])} faturas",
        help=f"Atendendo {formata_inteiro(kpi_data['clientes_unicos'])} clientes com {formata_inteiro(kpi_data['franqueados_ativos'])} franqueados."
    )

st.markdown("")

# --------------------------------------------------------------------------------------
# ABAS DE CONTEÚDO E ANÁLISE
# --------------------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📅 Evolução Histórica & Sazonalidade",
    "🎯 Curva ABC (Concentração de Carteira)",
    "👥 Performance da Rede de Vendas"
])

# --------------------------------------------------------------------------------------
# ABA 1: EVOLUÇÃO TEMPORAL
# --------------------------------------------------------------------------------------
with tab1:
    col_chart1, col_chart2 = st.columns([7, 5])
    
    query_mes = f"""
    SELECT 
        CAST(AnoMes AS VARCHAR) as AnoMes,
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
    
    with col_chart1:
        if not df_mes.empty:
            fig_evolucao = px.area(
                df_mes,
                x="AnoMes",
                y="Faturamento",
                markers=True,
                title="Evolução Mensal da Receita Bruta",
                labels={"AnoMes": "Competência (Ano/Mês)", "Faturamento": "Receita Bruta (R$)"},
                color_discrete_sequence=["#2563EB"]
            )
            fig_evolucao.update_layout(
                separators=",.",
                height=380,
                margin=dict(l=20, r=20, t=50, b=30),
                hovermode="x unified"
            )
            fig_evolucao.update_traces(
                hovertemplate="Faturamento: R$ %{y:,.2f}<extra></extra>"
            )
            st.plotly_chart(fig_evolucao, use_container_width=True)
        else:
            st.info("Sem dados para os filtros selecionados.")
            
    with col_chart2:
        query_ano = f"""
        SELECT 
            CAST(ANO AS VARCHAR) as Ano,
            ROUND(SUM(ValorTotalServico), 2) as Faturamento,
            COUNT(*) as Qtd_Faturas,
            ROUND(AVG(ValorTotalServico), 2) as Ticket_Medio
        FROM faturamento
        {where_sql}
        GROUP BY ANO
        ORDER BY ANO
        """
        df_ano = con.execute(query_ano).df()
        
        if not df_ano.empty:
            fig_ano = px.bar(
                df_ano,
                x="Ano",
                y="Faturamento",
                text="Faturamento",
                title="Consolidação Anual",
                color_discrete_sequence=["#4F46E5"]
            )
            fig_ano.update_layout(
                separators=",.",
                height=380,
                margin=dict(l=20, r=20, t=50, b=30)
            )
            fig_ano.update_traces(
                texttemplate="R$ %{y:,.2s}",
                textposition="outside",
                hovertemplate="Ano %{x}: R$ %{y:,.2f}<extra></extra>"
            )
            st.plotly_chart(fig_ano, use_container_width=True)

# --------------------------------------------------------------------------------------
# ABA 2: CURVA ABC / PARETO
# --------------------------------------------------------------------------------------
with tab2:
    st.markdown("##### Concentração e Risco de Dependência (Princípio de Pareto)")
    st.caption("Classificação dos clientes pela representatividade sobre a receita total acumulada.")
    
    query_pareto = f"""
    WITH fat_cli AS (
        SELECT 
            Cliente,
            COUNT(*) as Qtd_Faturas,
            ROUND(SUM(ValorTotalServico), 2) as Faturamento,
            ROUND(AVG(ValorTotalServico), 2) as Ticket_Medio
        FROM faturamento
        {where_sql}
        GROUP BY Cliente
    ),
    acum AS (
        SELECT 
            Cliente,
            Qtd_Faturas,
            Faturamento,
            Ticket_Medio,
            SUM(Faturamento) OVER (ORDER BY Faturamento DESC) as S_Acum,
            SUM(Faturamento) OVER () as S_Total
        FROM fat_cli
    )
    SELECT 
        Cliente,
        Qtd_Faturas,
        Faturamento,
        Ticket_Medio,
        ROUND((S_Acum / S_Total) * 100, 2) as Pct_Acumulado,
        CASE 
            WHEN (S_Acum / S_Total) <= 0.80 THEN 'Classe A (80% da Receita)'
            WHEN (S_Acum / S_Total) <= 0.95 THEN 'Classe B (15% da Receita)'
            ELSE 'Classe C (5% Cauda Longa)'
        END as Classe
    FROM acum
    ORDER BY Faturamento DESC
    """
    df_pareto = con.execute(query_pareto).df()
    
    if not df_pareto.empty:
        col_abc_pie, col_abc_table = st.columns([5, 7])
        
        with col_abc_pie:
            dist_classe = df_pareto.groupby("Classe")["Faturamento"].sum().reset_index()
            fig_pie = px.pie(
                dist_classe,
                names="Classe",
                values="Faturamento",
                hole=0.45,
                title="Participação por Faixa de Risco",
                color="Classe",
                color_discrete_map={
                    'Classe A (80% da Receita)': '#10B981',
                    'Classe B (15% da Receita)': '#F59E0B',
                    'Classe C (5% Cauda Longa)': '#64748B'
                }
            )
            fig_pie.update_layout(
                separators=",.",
                height=350,
                margin=dict(l=10, r=10, t=50, b=20)
            )
            fig_pie.update_traces(
                textinfo="percent+label",
                hovertemplate="%{label}<br>R$ %{value:,.2f} (%{percent})<extra></extra>"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_abc_table:
            st.markdown("###### Top 10 Clientes Estratégicos")
            tabela_exibicao = df_pareto.head(10).copy()
            tabela_exibicao['Faturamento'] = tabela_exibicao['Faturamento'].apply(formata_brl)
            tabela_exibicao['Ticket_Medio'] = tabela_exibicao['Ticket_Medio'].apply(formata_brl)
            tabela_exibicao['Pct_Acumulado'] = tabela_exibicao['Pct_Acumulado'].apply(formata_percentual)
            
            st.dataframe(
                tabela_exibicao[['Cliente', 'Faturamento', 'Ticket_Medio', 'Pct_Acumulado', 'Classe']],
                hide_index=True,
                use_container_width=True
            )

# --------------------------------------------------------------------------------------
# ABA 3: FRANQUEADOS
# --------------------------------------------------------------------------------------
with tab3:
    st.markdown("##### Ranking de Vendas por Franqueado")
    
    query_franq = f"""
    SELECT 
        Vendedor as Franqueado,
        COUNT(*) as Total_Faturas,
        COUNT(DISTINCT Cliente) as Clientes_Atendidos,
        ROUND(SUM(ValorTotalServico), 2) as Faturamento_Total,
        ROUND(AVG(ValorTotalServico), 2) as Ticket_Medio
    FROM faturamento
    {where_sql}
    GROUP BY Vendedor
    ORDER BY Faturamento_Total ASC
    """
    df_franq = con.execute(query_franq).df()
    
    if not df_franq.empty:
        col_rank_chart, col_rank_table = st.columns([6, 6])
        
        with col_rank_chart:
            top_franq = df_franq.tail(10)
            fig_franq = px.bar(
                top_franq,
                x="Faturamento_Total",
                y="Franqueado",
                orientation='h',
                title="Top 10 Franqueados (Receita Total)",
                color="Faturamento_Total",
                color_continuous_scale="Blues"
            )
            fig_franq.update_layout(
                separators=",.",
                height=420,
                margin=dict(l=20, r=20, t=50, b=20),
                coloraxis_showscale=False
            )
            fig_franq.update_traces(
                hovertemplate="<b>%{y}</b><br>Faturamento: R$ %{x:,.2f}<extra></extra>"
            )
            st.plotly_chart(fig_franq, use_container_width=True)
            
        with col_rank_table:
            st.markdown("###### Detalhamento Geral da Rede")
            tabela_franq = df_franq.sort_values(by="Faturamento_Total", ascending=False).copy()
            tabela_franq['Faturamento_Total'] = tabela_franq['Faturamento_Total'].apply(formata_brl)
            tabela_franq['Ticket_Medio'] = tabela_franq['Ticket_Medio'].apply(formata_brl)
            tabela_franq['Total_Faturas'] = tabela_franq['Total_Faturas'].apply(formata_inteiro)
            tabela_franq['Clientes_Atendidos'] = tabela_franq['Clientes_Atendidos'].apply(formata_inteiro)
            
            st.dataframe(
                tabela_franq,
                hide_index=True,
                use_container_width=True
            )

# Rodapé profissional
st.markdown("---")
st.caption("Desenvolvido por Caroline Rocha | Análise de Inteligência Comercial com Python, DuckDB e Streamlit")
