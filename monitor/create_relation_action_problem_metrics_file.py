import pandas as pd
import json
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

# Caminhos dos arquivos de entrada e saída
PROBLEMAS_PATH = "/Users/matius/Documents/maloka/agents/agente-analista-estoque/database/problemas_identificados.csv"
ACOES_PATH = "../database/acoes_planejamento.csv"
METRICAS_PATH = '../database/relacao_relevancia_planejamento_metrica.csv'
EG_OUTPUT_FILE_PATH = './artefacts/relation_action_problem_metrics_eg.json'
OUTPUT_PATH = './output/relation_action_problem_metrics.json'

# Carregar dados
problemas_df = pd.read_csv(PROBLEMAS_PATH)
acoes_df = pd.read_csv(ACOES_PATH)
metricas_df = pd.read_csv(METRICAS_PATH)
with open(EG_OUTPUT_FILE_PATH, 'r') as f:
    example_output_json = json.load(f)
print(example_output_json)

# Preparar textos para o prompt
problemas_txt = '\n'.join(f"{row.id_problema:2d}: {row.desc_problema}" for _, row in problemas_df.iterrows())
acoes_txt = '\n'.join(f"{row.id_acao:2d}: {row.desc_acao}" for _, row in acoes_df.iterrows())
metricas_txt = '\n'.join(f"{row['nome_metrica']}" for idx, row in metricas_df.iterrows())

# Montar prompt
prompt = f"""
Você é um analista de dados especialista em planejamento de estoques. Relacione os problemas, ações e métricas abaixo, criando um mapeamento estruturado.

Problemas:\n{problemas_txt}
\nAções:\n{acoes_txt}
\nMétricas:\n{metricas_txt}

Para cada problema, indique quais ações e métricas estão relacionadas. Para cada ação, indique as métricas que ela impacta. Utilize apenas as métricas que foram fornecidas com o exato nome fornecido 
Use o seguinte formato JSON:
- {example_output_json}

Responda apenas com o JSON, com os valores de ids e nome das metricsa vindos dos arquivos que passei.
"""

# Rodar LLM
SYSTEM_PROMPT = """ 
Você é o *Agente Monitor de Planejamento de Estoque*.

Objetivo:
1. Avaliar o progresso do planejamento.
2. Confrontar a situação atual com:
   • linha de base  
   • metas fixadas
   • projeções estatísticas para o período
3. Identificar tendências, riscos, desvios.
4. Propor ajustes de ações ou novas ações.

Restrições:
- Fundamente-se exclusivamente nos resumos de dados passados na entrada.
- Sempre devolva um JSON com as chaves exigidas em cada subtarefa."""
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
messages = [
    SystemMessage(content="Você é um analista de dados especialista em planejamento de estoques."),
    HumanMessage(content=prompt)
]
resposta = llm(messages).content

# Tentar converter resposta para JSON
try:
    if resposta.strip().startswith('```json'):
        resposta = resposta.strip()[7:]
    if resposta.strip().endswith('```'):
        resposta = resposta.strip()[:-3]
    output = json.loads(resposta)
except Exception:
    output = {"erro": "Resposta não está em JSON", "resposta": resposta}

# Salvar arquivo de saída
with open(OUTPUT_PATH, 'w') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Arquivo de saída gerado em {OUTPUT_PATH}")

