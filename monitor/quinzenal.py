import pandas as pd
import numpy as np
import os
import sys
import json
import glob
import re
from datetime import datetime
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from typing import Dict, List, Any, Optional, Tuple
import logging
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from io import BytesIO
import base64

# Configuração básica
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class InventoryTrackingAgent:
    """
    Agente de acompanhamento quinzenal para monitorar a evolução das métricas de estoque
    e avaliar o progresso das ações implementadas.
    """
    
    def __init__(self, openai_api_key: str = None, model_name: str = "gpt-4o", temp=0.2):
        """
        Inicializa o agente de acompanhamento.
        
        Args:
            openai_api_key: Chave da API OpenAI (padrão para variável de ambiente)
            model_name: Nome do modelo OpenAI a ser usado
            temp: Temperatura para o modelo LLM
        """
        self.api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.model_name = model_name
        self.temp = temp
        self.llm = ChatOpenAI(
            temperature=temp, 
            model_name=self.model_name,
            openai_api_key=self.api_key
        )
        
        # Criação dos prompts e chains
        self.metrics_analysis_prompt = self._create_metrics_analysis_prompt()
        self.action_tracking_prompt = self._create_action_tracking_prompt()
        self.report_generation_prompt = self._create_report_generation_prompt()
        
        self.metrics_analysis_chain = LLMChain(llm=self.llm, prompt=self.metrics_analysis_prompt)
        self.action_tracking_chain = LLMChain(llm=self.llm, prompt=self.action_tracking_prompt)
        self.report_generation_chain = LLMChain(llm=self.llm, prompt=self.report_generation_prompt)
        
        # Armazenamento de dados processados
        self.metrics_history = {}
        self.baseline_metrics = {}
        self.current_metrics = {}
        self.action_plan = {}
        self.problem_analysis = {}
        self.cycle_count = 0
    
    def _create_metrics_analysis_prompt(self) -> PromptTemplate:
        """Cria o prompt para analisar a evolução das métricas."""
        template = """
        Como especialista em gestão de estoque, analise a evolução das métricas de estoque ao longo do tempo.
        
        ## Métricas Iniciais (Linha de Base)
        ```json
        {baseline_metrics}
        ```
        
        ## Métricas Atuais
        ```json
        {current_metrics}
        ```
        
        ## Histórico de Métricas
        ```json
        {metrics_history}
        ```
        
        ## Metas Estabelecidas
        ```json
        {target_metrics}
        ```
        
        ## Instruções
        1. Compare as métricas atuais com a linha de base e identifique as principais variações
        2. Avalie o progresso em relação às metas estabelecidas
        3. Identifique tendências (positivas ou negativas) nas métricas-chave
        4. Destaque os desvios significativos do plano original
        5. Calcule a taxa de progresso para cada métrica-chave (porcentagem do caminho em direção à meta)
        
        ## Formato de Saída
        Forneça sua análise como um objeto JSON com a seguinte estrutura:
        ```json
        {
          "metrics_comparison": [
            {
              "metric_name": "Nome da métrica",
              "baseline_value": valor_inicial,
              "current_value": valor_atual,
              "target_value": valor_meta,
              "absolute_change": mudança_absoluta,
              "percentage_change": "mudança_percentual%",
              "progress_rate": "taxa_de_progresso%",
              "trend": "increasing/decreasing/stable",
              "status": "on_track/at_risk/off_track",
              "insights": "Análise específica desta métrica"
            }
          ],
          "overall_assessment": {
            "overall_progress": "taxa_global_de_progresso%",
            "on_track_metrics": número_métricas_no_caminho,
            "at_risk_metrics": número_métricas_em_risco,
            "off_track_metrics": número_métricas_fora_do_caminho,
            "key_achievements": ["conquista1", "conquista2"],
            "key_concerns": ["preocupação1", "preocupação2"]
          },
          "trends_identified": [
            {
              "trend_description": "Descrição da tendência",
              "affected_metrics": ["métrica1", "métrica2"],
              "potential_impact": "Impacto potencial desta tendência",
              "recommendation": "Recomendação relacionada a esta tendência"
            }
          ]
        }
        ```
        
        Forneça uma análise profunda baseada em dados, com insights quantitativos e qualitativos.
        """
        
        return PromptTemplate(
            input_variables=["baseline_metrics", "current_metrics", "metrics_history", "target_metrics"],
            template=template
        )
    
    def _create_action_tracking_prompt(self) -> PromptTemplate:
        """Cria o prompt para acompanhar as ações do plano original."""
        template = """
        Como especialista em gestão de estoque, avalie o progresso das ações implementadas com base na evolução das métricas.
        
        ## Plano de Ação Original
        ```markdown
        {action_plan}
        ```
        
        ## Análise de Problemas Original
        ```markdown
        {problem_analysis}
        ```
        
        ## Evolução das Métricas
        ```json
        {metrics_evolution}
        ```
        
        ## Instruções
        1. Para cada ação no plano original, avalie seu status atual com base na evolução das métricas relacionadas
        2. Determine se cada ação está: Completa, Em Andamento, Atrasada ou Não Iniciada
        3. Calcule o impacto financeiro observado para as ações em andamento ou completas
        4. Identifique obstáculos potenciais para ações atrasadas ou não iniciadas
        5. Sugira ajustes ou novas ações com base nos resultados observados
        
        ## Formato de Saída
        Forneça sua avaliação como um objeto JSON com a seguinte estrutura:
        ```json
        {
          "action_status": [
            {
              "problem": "Descrição do problema",
              "action": "Descrição da ação",
              "status": "complete/in_progress/delayed/not_started",
              "completion_percentage": percentual_de_conclusão,
              "related_metrics": ["métrica1", "métrica2"],
              "observed_impact": "Impacto observado até o momento",
              "financial_impact": "Estimativa do impacto financeiro observado",
              "obstacles": ["obstáculo1", "obstáculo2"],
              "recommended_adjustments": "Ajustes recomendados para esta ação"
            }
          ],
          "overall_plan_status": {
            "actions_complete": número_ações_completas,
            "actions_in_progress": número_ações_em_andamento,
            "actions_delayed": número_ações_atrasadas,
            "actions_not_started": número_ações_não_iniciadas,
            "overall_completion": "percentual_global_de_conclusão%",
            "financial_impact_to_date": "Impacto financeiro total observado até o momento"
          },
          "new_actions_recommended": [
            {
              "problem": "Problema relacionado",
              "action_description": "Descrição da nova ação recomendada",
              "rationale": "Justificativa para esta nova ação",
              "expected_impact": "Impacto esperado desta ação",
              "priority": "high/medium/low"
            }
          ]
        }
        ```
        
        Forneça uma avaliação objetiva baseada em evidências quantitativas das métricas.
        """
        
        return PromptTemplate(
            input_variables=["action_plan", "problem_analysis", "metrics_evolution"],
            template=template
        )
    
    def _create_report_generation_prompt(self) -> PromptTemplate:
        """Cria o prompt para gerar o relatório quinzenal de acompanhamento."""
        template = """
        Como especialista em gestão de estoque, crie um relatório quinzenal detalhado de acompanhamento do plano de ação.
        
        ## Análise de Métricas
        ```json
        {metrics_analysis}
        ```
        
        ## Status das Ações
        ```json
        {action_status}
        ```
        
        ## Ciclo de Acompanhamento
        Ciclo: {cycle_number}
        Data: {report_date}
        
        ## Instruções
        Crie um relatório quinzenal completo que inclua:
        1. Resumo executivo do progresso geral
        2. Tabela de evolução das métricas-chave (comparando linha base, meta e valor atual)
        3. Status atualizado de cada ação do plano original
        4. Tendências identificadas e suas implicações
        5. Recomendações para ajustes no plano
        6. Previsão para o próximo período
        
        ## Formato de Saída
        Forneça o relatório em formato markdown estruturado e profissional.
        Utilize tabelas, listas e formatação para facilitar a leitura.
        Inclua símbolos visuais para indicar status (🟢 No caminho, 🟡 Em progresso, 🟠 Atrasado, 🔴 Crítico).
        
        O relatório deve ser detalhado, baseado em dados, mas também acessível para gestores de negócios.
        Foque em insights acionáveis e recomendações concretas.
        """
        
        return PromptTemplate(
            input_variables=["metrics_analysis", "action_status", "cycle_number", "report_date"],
            template=template
        )
    
    def load_data(self, 
                  scenario_pattern: str, 
                  action_plan_path: str, 
                  problem_analysis_path: str) -> None:
        """
        Carrega todos os dados necessários para o acompanhamento.
        
        Args:
            scenario_pattern: Padrão para encontrar arquivos de cenário (ex: "./cenarios/cenario1_*.json")
            action_plan_path: Caminho para o arquivo do plano de ação
            problem_analysis_path: Caminho para o arquivo de análise de problemas
        """
        logging.info(f"Carregando dados para análise...")
        
        # Carrega cenários de métricas
        scenario_files = sorted(glob.glob(scenario_pattern))
        if not scenario_files:
            raise ValueError(f"Nenhum arquivo de cenário encontrado com o padrão: {scenario_pattern}")
        
        # Extrai o número de versão do padrão de nome de arquivo
        def extract_version(filename):
            match = re.search(r'_(\d+)\.json$', filename)
            return int(match.group(1)) if match else 0
        
        # Ordena os arquivos por número de versão
        scenario_files.sort(key=extract_version)
        
        # Carrega todos os cenários
        for file in scenario_files:
            version = extract_version(file)
            with open(file, "r") as f:
                metrics_data = json.load(f)
                self.metrics_history[version] = metrics_data
                
                # O primeiro cenário é a linha de base
                if version == 0:
                    self.baseline_metrics = metrics_data
                
                # O último cenário é o atual
                self.current_metrics = metrics_data
        
        # Carrega o plano de ação
        try:
            with open(action_plan_path, "r") as f:
                self.action_plan = f.read()
        except Exception as e:
            raise ValueError(f"Erro ao carregar o plano de ação: {e}")
        
        # Carrega a análise de problemas
        try:
            with open(problem_analysis_path, "r") as f:
                self.problem_analysis = f.read()
        except Exception as e:
            raise ValueError(f"Erro ao carregar a análise de problemas: {e}")
        
        # Extrai metas do plano de ação
        self.target_metrics = self._extract_targets_from_action_plan()
        
        logging.info(f"Dados carregados com sucesso: {len(self.metrics_history)} cenários, plano de ação e análise de problemas")
    
    def load_data_from_database(self, database_path: str, contratante: str,
                                action_plan_path: str = None, problem_analysis_path: str = None) -> None:
        """
        Carrega os dados do CSV de banco de dados para o acompanhamento, filtrando pelo contratante.
        """
        import csv
        self.metrics_history = {}
        self.baseline_metrics = None
        self.current_metrics = None
        with open(database_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = [row for row in reader if row['contratante'] == contratante]
            if not rows:
                raise ValueError(f"Nenhuma linha encontrada para contratante: {contratante}")
            for idx, row in enumerate(rows):
                metrics = {k: self._try_parse_number(v) for k, v in row.items() if k != 'contratante'}
                self.metrics_history[idx] = metrics
                if idx == 0:
                    self.baseline_metrics = metrics
                self.current_metrics = metrics
        self.cycle_count = len(rows)
        # Carrega plano de ação e análise de problemas (como no load_data)
        if action_plan_path:
            with open(action_plan_path, "r") as f:
                self.action_plan = f.read()
        else:
            self.action_plan = ""
        if problem_analysis_path:
            with open(problem_analysis_path, "r") as f:
                self.problem_analysis = f.read()
        else:
            self.problem_analysis = ""
        self.target_metrics = self._extract_targets_from_action_plan()

    @staticmethod
    def _try_parse_number(value):
        try:
            if value is None or value == '':
                return None
            if '.' in value or 'e' in value.lower():
                return float(value)
            return int(value)
        except Exception:
            return value
    
    def _extract_targets_from_action_plan(self) -> Dict[str, Any]:
        """
        Extrai as métricas-alvo definidas no plano de ação.
        
        Returns:
            Dicionário com as métricas-alvo extraídas
        """
        target_metrics = {}
        
        # Padrão para encontrar KPIs alvo no markdown
        kpi_pattern = r"(?:- \*\*KPIs Alvo\*\*:[\s\n]+((?:  - [^\n]+\n)+))"
        
        # Encontra todos os blocos de KPIs alvo
        kpi_blocks = re.findall(kpi_pattern, self.action_plan)
        
        # Para cada bloco, extrai os KPIs individuais
        for block in kpi_blocks:
            kpi_entries = re.findall(r"  - ([^:]+): ([^\n]+)", block)
            for kpi_name, kpi_value in kpi_entries:
                # Limpa e normaliza os valores
                kpi_name = kpi_name.strip()
                
                # Remove símbolos de porcentagem e cifrão para converter para número
                value = kpi_value.strip()
                value = value.replace("%", "").replace("$", "").replace(",", "")
                
                try:
                    # Tenta converter para número se possível
                    if "." in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    # Mantém como string se não for possível converter
                    pass
                
                target_metrics[kpi_name] = value
        
        logging.info(f"Extraídas {len(target_metrics)} métricas-alvo do plano de ação")
        return target_metrics
    
    def analyze_metrics(self) -> Dict[str, Any]:
        """
        Analisa a evolução das métricas ao longo do tempo.
        
        Returns:
            Análise de métricas em formato JSON
        """
        logging.info("Analisando evolução das métricas...")
        
        # Prepara inputs para o chain
        inputs = {
            "baseline_metrics": json.dumps(self.baseline_metrics, indent=2),
            "current_metrics": json.dumps(self.current_metrics, indent=2),
            "metrics_history": json.dumps(self.metrics_history, indent=2),
            "target_metrics": json.dumps(self.target_metrics, indent=2)
        }
        
        # Executa a análise
        analysis_result = self.metrics_analysis_chain.run(**inputs)
        
        # Limpa e converte o resultado para JSON
        cleaned_result = self._clean_json_string(analysis_result)
        try:
            metrics_analysis = json.loads(cleaned_result)
            logging.info("Análise de métricas concluída com sucesso")
            return metrics_analysis
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar a análise de métricas: {e}")
            logging.error(f"Resultado limpo: {cleaned_result}")
            raise ValueError(f"Falha ao analisar métricas: {e}")
    
    def track_actions(self, metrics_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Acompanha o status das ações do plano original.
        
        Args:
            metrics_analysis: Análise de métricas gerada pelo método analyze_metrics
            
        Returns:
            Status das ações em formato JSON
        """
        logging.info("Acompanhando status das ações...")
        
        # Prepara inputs para o chain
        inputs = {
            "action_plan": self.action_plan,
            "problem_analysis": self.problem_analysis,
            "metrics_evolution": json.dumps(metrics_analysis, indent=2)
        }
        
        # Executa o acompanhamento
        action_result = self.action_tracking_chain.run(**inputs)
        
        # Limpa e converte o resultado para JSON
        cleaned_result = self._clean_json_string(action_result)
        try:
            action_status = json.loads(cleaned_result)
            logging.info("Acompanhamento de ações concluído com sucesso")
            return action_status
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar o status das ações: {e}")
            logging.error(f"Resultado limpo: {cleaned_result}")
            raise ValueError(f"Falha ao acompanhar ações: {e}")
    
    def generate_report(self, 
                        metrics_analysis: Dict[str, Any], 
                        action_status: Dict[str, Any], 
                        cycle_number: int,
                        output_path: str) -> str:
        """
        Gera o relatório quinzenal de acompanhamento.
        
        Args:
            metrics_analysis: Análise de métricas
            action_status: Status das ações
            cycle_number: Número do ciclo de acompanhamento (1, 2, 3, etc.)
            output_path: Caminho para salvar o relatório gerado
            
        Returns:
            Relatório em formato markdown
        """
        logging.info(f"Gerando relatório para o ciclo {cycle_number}...")
        
        # Prepara a data do relatório (atual)
        report_date = datetime.now().strftime("%d/%m/%Y")
        
        # Prepara inputs para o chain
        inputs = {
            "metrics_analysis": json.dumps(metrics_analysis, indent=2),
            "action_status": json.dumps(action_status, indent=2),
            "cycle_number": str(cycle_number),
            "report_date": report_date
        }
        
        # Gera o relatório
        report = self.report_generation_chain.run(**inputs)
        
        # Salva o relatório
        with open(output_path, "w") as f:
            f.write(report)
        
        logging.info(f"Relatório gerado e salvo em: {output_path}")
        return report
    
    def generate_metrics_dashboard(self, 
                                   metrics_analysis: Dict[str, Any], 
                                   output_path: str) -> None:
        """
        Gera um dashboard visual das métricas principais.
        
        Args:
            metrics_analysis: Análise de métricas
            output_path: Caminho para salvar o dashboard
        """
        logging.info("Gerando dashboard de métricas...")
        
        try:
            # Extrai os dados de métricas da análise
            metrics_data = metrics_analysis.get("metrics_comparison", [])
            
            if not metrics_data:
                logging.warning("Nenhum dado de métrica encontrado para gerar o dashboard")
                return
            
            # Limita a no máximo 6 métricas para o dashboard
            metrics_data = metrics_data[:6]
            
            # Cria uma figura com 2 gráficos
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))
            
            # Gráfico 1: Valores atuais vs metas
            metric_names = [m["metric_name"] for m in metrics_data]
            current_values = [m["current_value"] for m in metrics_data]
            target_values = [m["target_value"] for m in metrics_data]
            
            x = range(len(metric_names))
            width = 0.35
            
            ax1.bar([i - width/2 for i in x], current_values, width, label='Valor Atual')
            ax1.bar([i + width/2 for i in x], target_values, width, label='Meta')
            
            ax1.set_title('Valores Atuais vs Metas')
            ax1.set_xticks(x)
            ax1.set_xticklabels(metric_names, rotation=45, ha='right')
            ax1.legend()
            
            # Gráfico 2: Taxa de progresso
            progress_rates = [float(m["progress_rate"].replace("%", "")) for m in metrics_data]
            
            # Cores baseadas no progresso
            colors = ['#ff9999' if rate < 30 else '#ffcc99' if rate < 70 else '#99cc99' for rate in progress_rates]
            
            ax2.barh(metric_names, progress_rates, color=colors)
            ax2.set_title('Taxa de Progresso (%)')
            ax2.set_xlim(0, 100)
            ax2.axvline(x=50, color='gray', linestyle='--')
            
            # Adiciona rótulos de porcentagem
            for i, v in enumerate(progress_rates):
                ax2.text(v + 3, i, f"{v}%", va='center')
            
            plt.tight_layout()
            plt.savefig(output_path)
            
            logging.info(f"Dashboard de métricas gerado e salvo em: {output_path}")
            
        except Exception as e:
            logging.error(f"Erro ao gerar dashboard de métricas: {e}")
    
    def generate_action_status_dashboard(self, 
                                         action_status: Dict[str, Any], 
                                         output_path: str) -> None:
        """
        Gera um dashboard visual do status das ações.
        
        Args:
            action_status: Status das ações
            output_path: Caminho para salvar o dashboard
        """
        logging.info("Gerando dashboard de status das ações...")
        
        try:
            # Extrai os dados de status do plano
            overall_status = action_status.get("overall_plan_status", {})
            
            if not overall_status:
                logging.warning("Nenhum dado de status encontrado para gerar o dashboard")
                return
            
            # Extrai os números
            complete = overall_status.get("actions_complete", 0)
            in_progress = overall_status.get("actions_in_progress", 0)
            delayed = overall_status.get("actions_delayed", 0)
            not_started = overall_status.get("actions_not_started", 0)
            
            # Cria a figura
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))
            
            # Gráfico 1: Pizza de status das ações
            labels = ['Completas', 'Em Andamento', 'Atrasadas', 'Não Iniciadas']
            sizes = [complete, in_progress, delayed, not_started]
            colors = ['#99cc99', '#ffcc99', '#ff9999', '#dddddd']
            
            ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
                    startangle=90, wedgeprops={'edgecolor': 'white'})
            ax1.axis('equal')
            ax1.set_title('Status das Ações')
            
            # Gráfico 2: Taxa de conclusão do plano
            overall_completion = float(overall_status.get("overall_completion", "0").replace("%", ""))
            
            # Cria um gráfico de progresso
            ax2.barh(['Progresso Total'], [overall_completion], color='#aaddff')
            ax2.barh(['Progresso Total'], [100], color='#eeeeee')
            ax2.set_title('Conclusão Geral do Plano')
            ax2.set_xlim(0, 100)
            
            # Adiciona rótulo de porcentagem
            ax2.text(overall_completion + 3, 0, f"{overall_completion}%", va='center')
            
            plt.tight_layout()
            plt.savefig(output_path)
            
            logging.info(f"Dashboard de status das ações gerado e salvo em: {output_path}")
            
        except Exception as e:
            logging.error(f"Erro ao gerar dashboard de status das ações: {e}")
    
    def _clean_json_string(self, json_string: str) -> str:
        """
        Limpa uma string JSON de possíveis elementos de formatação.
        
        Args:
            json_string: String JSON a ser limpa
            
        Returns:
            String JSON limpa
        """
        # Remove blocos de código markdown
        json_string = re.sub(r'```json\s*', '', json_string)
        json_string = re.sub(r'```\s*', '', json_string)
        
        # Limpa espaços extras no início e fim
        json_string = json_string.strip()
        
        return json_string
    
    def run_analysis_cycle(self, 
                        scenario_pattern: str, 
                        action_plan_path: str, 
                        problem_analysis_path: str,
                        cycle_number: int,
                        output_dir: str = "./output") -> Dict[str, str]:
        """
        Executa um ciclo completo de análise e gera todos os relatórios.
        """
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, f"relatorio_quinzenal_ciclo_{cycle_number}.md")
        metrics_dashboard_path = os.path.join(output_dir, f"dashboard_metricas_ciclo_{cycle_number}.png")
        actions_dashboard_path = os.path.join(output_dir, f"dashboard_acoes_ciclo_{cycle_number}.png")

        # Só carrega dados se scenario_pattern não for None (modo antigo)
        if scenario_pattern is not None:
            self.load_data(scenario_pattern, action_plan_path, problem_analysis_path)

        metrics_analysis = self.analyze_metrics()
        action_status = self.track_actions(metrics_analysis)
        report = self.generate_report(metrics_analysis, action_status, cycle_number, report_path)
        self.generate_metrics_dashboard(metrics_analysis, metrics_dashboard_path)
        self.generate_action_status_dashboard(action_status, actions_dashboard_path)

        return {
            "report": report_path,
            "metrics_dashboard": metrics_dashboard_path,
            "actions_dashboard": actions_dashboard_path
        }

def main():
    """Função principal para executar o agente de acompanhamento quinzenal."""
    print("=== AGENTE DE ACOMPANHAMENTO QUINZENAL DE ESTOQUE ===")
    print("Este agente analisa a evolução das métricas de estoque e acompanha o progresso das ações implementadas.")

    # Novo fluxo para usar database.csv
    database_path = str(input("Digite o caminho para o arquivo database.csv (ex: './cenarios/database.csv'): ")) or "./cenarios/database.csv"
    contratante = str(input("Digite o nome do contratante (ex: 'a_0'): "))
    action_plan_path = str(input("Digite o caminho para o arquivo do plano de ação (ex: './plans/action_plan_pt_cenario_a.md'): ")) or "./plans/action_plan_pt_cenario_a.md"
    problem_analysis_path = str(input("Digite o caminho para o arquivo de análise de problemas (ex: './plans/problem_analysis_pt_cenario_a.md'): ")) or "./plans/problem_analysis_pt_cenario_a.md"
    output_dir = input("Digite o diretório de saída para os relatórios (ex: './output'): ") or "./output"

    try:
        agent = InventoryTrackingAgent(model_name="gpt-4o", temp=0.2)
        agent.load_data_from_database(database_path, contratante, action_plan_path, problem_analysis_path)
        cycle_number = getattr(agent, 'cycle_count', 1)
        # Executa o ciclo de análise
        output_files = agent.run_analysis_cycle(
            scenario_pattern=None,  # Não usado neste fluxo
            action_plan_path=action_plan_path,
            problem_analysis_path=problem_analysis_path,
            cycle_number=cycle_number,
            output_dir=output_dir
        )
        print("\n=== ANÁLISE CONCLUÍDA COM SUCESSO ===")
        print(f"Relatório quinzenal: {output_files['report']}")
        print(f"Dashboard de métricas: {output_files['metrics_dashboard']}")
        print(f"Dashboard de status das ações: {output_files['actions_dashboard']}")
    except Exception as e:
        print(f"\nERRO: {e}")
        logging.error(f"Erro na execução do agente: {e}", exc_info=True)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())