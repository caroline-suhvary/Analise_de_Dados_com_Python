Título do Case: Análise de Faturamento e Performance Comercial (2021–2024)
Link 1:
🌐 Dashboard Interativo Online (Streamlit) — para quem quer mexer nos filtros e ver os gráficos.
Link 2:
📓 Caderno de Análise e Consultas SQL/DuckDB (Jupyter Notebook) — para quem quer ver seu código aprofundado, modelagem e lógica de análise.

# 📊 Projeto de Inteligência Comercial e Faturamento (Python + DuckDB + Streamlit)

Este projeto foi desenvolvido para transformar dados transacionais de faturamento de ERP em um painel interativo de inteligência comercial, focado em tomada de decisão gerencial e análise de concentração de clientes (Pareto 80/20).

## 🚀 Tecnologias Utilizadas

- **Python 3.10+**
- **DuckDB:** Consultas analíticas ultrarrápidas com SQL diretamente em arquivos colunares.
- **Streamlit:** Construção e publicação de dashboards analíticos interativos.
- **Plotly:** Visualizações e gráficos dinâmicos.
- **Apache Parquet:** Formato colunar de alta performance para armazenamento e consulta.

---

## 📁 Estrutura do Repositório

- `app.py`: Aplicação web interativa no Streamlit.
- `caderno_analise.py`: Script passo a passo com comentários explicativos de cada etapa de ETL, métricas e consultas SQL (estilo Google Colab / Notebook).
- `faturamento.parquet`: Base de dados transacional limpa e anonimizada (7.873 faturas, 2021 a 2024).
- `requirements.txt`: Dependências necessárias para executar o projeto.

---

## 🛠️ Como Executar Localmente

1. Clone este repositório:
   ```bash
   git clone https://github.com/SEU-USUARIO/NOME-DO-REPOSITORIO.git
   cd NOME-DO-REPOSITORIO
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute o dashboard no Streamlit:
   ```bash
   streamlit run app.py
   ```

---

## 🌐 Como Publicar Gratuitamente no Streamlit Cloud

1. Crie um repositório no seu GitHub e suba os 4 arquivos (`app.py`, `faturamento.parquet`, `requirements.txt`, `README.md`).
2. Acesse [share.streamlit.io](https://share.streamlit.io) e faça login com seu GitHub.
3. Clique em **"New app"**.
4. Selecione o repositório, deixe o arquivo principal como `app.py` e clique em **"Deploy"**.
5. O Streamlit vai gerar um link público que você pode incluir diretamente no seu site portfólio!
