import streamlit as st
import pandas as pd
from langchain.chat_models import ChatOpenAI  # substitui OpenAI para modelos de chat
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
from datetime import datetime
import yaml
import os

load_dotenv()
# Caminho absoluto do config.yaml
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

# Carrega o config.yaml em variáveis globais
config = load_config()

# Exemplo de uso das variáveis globais
TEMPORALITY_DAYS = config.get('temporality_days', [7, 15, 30])
TEMPORALITY = config.get('temporality', 7)
ID_CONTRATANTE = config.get('id_bibi')
START_DATE= config.get('start_date_bibi')
END_DATE = config.get('end_date_bibi')

METRICS_PATH = os.getenv("metrics_path")
PLANO_PATH = os.getenv("plano_path")
api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Relatório Automático de Estoque", layout="wide")

st.title("📊 Relatório Automático de Estoque - Powered by GPT")
# Parâmetros do modelo e do relatório

# Carrega o arquivo CSV diretamente do METRICS_PATH
if os.path.exists(METRICS_PATH):
    csv_file = open(METRICS_PATH, "r", encoding="utf-8")
    st.success(f"Arquivo CSV carregado: {METRICS_PATH}")
else:
    csv_file = None
    st.error(f"Arquivo CSV não encontrado: {METRICS_PATH}")

# Carrega o arquivo JSON do plano diretamente do PLANO_PATH
if os.path.exists(PLANO_PATH):
    plano_file = open(PLANO_PATH, "rb")
    st.success(f"Arquivo JSON do plano carregado: {PLANO_PATH}")
else:
    plano_file = None
    st.info(f"Arquivo JSON do plano não encontrado: {PLANO_PATH}")



modelo = "o3-mini-2025-01-31"
btn_gerar = st.button("Gerar Relatório")

if csv_file and api_key and btn_gerar:
    # Carregar dados CSV
    df = pd.read_csv(csv_file)
    # Garante que a coluna está em datetime
    df["data_hora_analise"] = pd.to_datetime(df["data_hora_analise"])

    # Converte START_DATE para datetime.date se necessário
    if isinstance(START_DATE, str):
        start_date = pd.to_datetime(START_DATE).date()
    else:
        start_date = START_DATE

    end_date = datetime.today().date()

    # Filtra o DataFrame para datas entre START_DATE e hoje
    filtered_df = df[
        (df["data_hora_analise"].dt.date >= start_date) &
        (df["data_hora_analise"].dt.date <= end_date) &
        (df["id_contratante"] == ID_CONTRATANTE)
    ]
    st.subheader("🔎 Dados carregados:")
    st.dataframe(filtered_df, use_container_width=True)

    # Carregar plano se houver
    plano_acao = ""
    if plano_file:
        plano_acao = plano_file.read().decode("utf-8")
        st.caption("Plano de ação carregado!")

    # PREPARA O PROMPT
    prompt_str = """
Você é um analista de estoque. Com base nas métricas históricas (abaixo) e, se disponível, no plano de ação (json), produza um relatório objetivo, rápido e estruturado, cobrindo:
- Evolução dos principais indicadores entre a data inicial e final.
- Identificação do que melhorou, piorou ou permaneceu estável.
- Verificação se as metas foram atingidas.
- Recomendações práticas de ação (priorize D-O-I: Deep-dive, Ofensiva, Integração).
- Se possível, use um tom de leveza, breves pitadas de humor, e tabelas para visualização.

CSV de métricas (cabeçalho + últimas linhas):
{csv}

JSON do plano de ação (se houver):
{plano}
"""

    # Prepara só um recorte do CSV (para não explodir o contexto!)
    csv_str = str(filtered_df)

    prompt_final = prompt_str.format(
        csv=csv_str,
        plano=plano_acao
    )

    # Instancia o modelo LangChain+OpenAI
    llm = ChatOpenAI(
        openai_api_key=api_key,
        model=modelo,
        max_completion_tokens=1800,
        temperature=1, #o3-mini nao aceita parametro de temperatura, mas so funciona passando =1, NAO REMOVA
    )

    chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate.from_template("{input}")
    )

    resultado = chain.run({"input": prompt_final})
    
    st.success("Relatório pronto!")
    st.markdown(resultado, unsafe_allow_html=True)
    st.write("Resultado bruto:", resultado)
    if not resultado:
        st.error("Nenhum resultado foi retornado pelo modelo. Verifique a configuração da API ou o prompt.")
    # Removido o botão de download, apenas exibe o resultado na tela

else:
    st.info("clique em 'Gerar Relatório'.")

st.markdown("---")
st.caption("by Palheta & ChatGPT - BFFs <3")
